import gc
import random

import tmdbsimple as tmdb
from django.conf import settings

from api.models import Puzzle, Solution
from api.utils import (
    get_movie_cast_and_crew,
    get_movie_info,
    get_persons_filmography,
    get_persons_info,
    order_by_popularity_and_deduplicate,
)


def random_filmography_six_steps_away(movie_id):
    print(movie_id, end=': ')
    
    previous_movie_ids = set()
    previous_person_ids = set()

    # Execute three pairs of steps: cast/crew followed by film
    for i in range(3):
        cast_and_crew = get_movie_cast_and_crew(movie_id)
        cast_and_crew_ids = {person['id'] for person in cast_and_crew}
        # Choose a branch randomly that hasn't previously been followed
        person_id = random.choice(list(cast_and_crew_ids - previous_person_ids))
        # Don't randomly go backwards later
        previous_person_ids.add(person_id)
        person = [person for person in cast_and_crew if person['id'] == person_id][0]
        print(person['name'], end=' | ')

        filmography = get_persons_filmography(person_id)
        # Don't bother with movie steps on last iteration
        if i < 2:
            movie_ids = {movie['id'] for movie in filmography}
            # Choose a branch randomly that hasn't previously been followed
            movie_id = random.choice(list(movie_ids - previous_movie_ids))
            # Don't randomly go backwards later
            previous_movie_ids.add(movie_id)
            movie = [movie for movie in filmography if movie['id'] == movie_id][0]
            print(movie['title'], end=' | ')
    
    print()
    # The final value of `filmography` is a set of "end movies" six steps away from our start movie.
    for film in filmography[:25]:
        print(f'{film["id"]}: {film["title"]}')


# Jobs outside of this set are not well known and thus not useful in building solutions.
# There may be safe jobs missing from this list.
safe_jobs = {
    'Costumer',
    'Camera Operator',
    'Director',
    'Director of Photography',
    'Production Design',
    'Editor',
    'Producer',
    'Original Story',
    'Writer',
    'Original Music Composer',
    'Executive Producer',
    'Casting',
    'Makeup Artist',
    'Title Designer',
    'Production Assistant',
    'Special Effects Makeup Artist',
    'Costume Designer',
    'Music Supervisor',
    'Screenplay',
    'Art Direction',
    'Fight Choreographer',
    'Choreographer',
    'Prosthetics',
    'Co-Producer',
    'Costume Design',
    'Songs',
    'Novel',
    'Theatre Play',
    'Production Designer',
    'Story',
    'Second Unit Director',
    'Characters',
}


class Node:    
    class Type:
        PERSON = 'Person'
        FILM = 'Film'
        
    def __init__(self, node_id, name, parent):
        self.node_id = node_id
        self.name = name
        self.parent = parent
        self.children = []
        
    def __eq__(self, other):
        """
        People or Films with the same ID are considered the same.
        """
        return self.node_id == other.node_id and self.type == other.type
        
    def __hash__(self):
        return hash(self.__repr__())
    
    def __repr__(self):
        return f'{self.type} #{self.node_id}: {self.name}'
    
    def pprint(self, path):
        """
        Print the path from the starting node to this one in names.
        """
        path.append(self)
        if self.parent:
            self.parent.pprint(path)
        else:
            path.reverse()
            for node in path[:-1]:
                print(f'{node} > ', end=' ')
            print(path[-1])

    def path_array(self, path):
        """
        Print the path from the starting node to this one in IDs.
        """
        path.append(self.node_id)
        if self.parent:
            return self.parent.path_array(path)
        else:
            path.reverse()
            return path

    def get_depth(self):
        if not self.parent:
            return 0
        return self.parent.get_depth() + 1

class PersonNode(Node):
    def __init__(self, node_id, name=None, parent=None):
        if not name:
            name = get_persons_info(node_id)['name']
        super().__init__(node_id, name, parent)
        self.type = Node.Type.PERSON

    def make_request(self):
        tmdb.API_KEY = settings.TMDB_API_KEY
        person = tmdb.People(self.node_id)
        filmography = person.movie_credits()
        as_cast = filmography['cast']
        as_crew = filmography['crew']
        # Exclude some stuff that no one has ever seen.
        filmography = [movie for movie in as_cast + as_crew if movie.get('popularity', 0) > 5]
        return order_by_popularity_and_deduplicate(filmography)
        
    def populate_children(self):
        self.children = {FilmNode(c['id'], c['title'], self) for c in self.make_request()}
        
class FilmNode(Node):
    def __init__(self, node_id, name=None, parent=None):
        if not name:
            name = get_movie_info(node_id)['title']
        super().__init__(node_id, name, parent)
        self.type = Node.Type.FILM

    def make_request(self):
        tmdb.API_KEY = settings.TMDB_API_KEY
        movie = tmdb.Movies(self.node_id)
        credits = movie.credits()
        cast = credits['cast']
        # Exclude roles no one knows about.
        crew = [credit for credit in credits['crew'] if credit['job'] in safe_jobs]
        # Exclude unpopular people, this threshold is arbitrary.
        return [person for person in cast + crew if person.get('popularity', 0) > 1.5]

    def populate_children(self):
        self.children = {PersonNode(c['id'], c['name'], self) for c in self.make_request()}

def find_shortest_solution(start, end, save_to_db=False):
    """
    Find the shortest route between two Nodes.
    `start` and `end` attributes should be FilmNodes or PersonNodes.
    A quick test is:
     * FilmNode(744): Top Gun, to
     * FilmNode(817): Austin Powers: The Spy Who Shagged Me
    """
    to_check = [start]
    failed_to_find = False    
    checked = set()
    
    while to_check:
        current_node = to_check.pop(0)
        current_node.populate_children()
        to_check += list(current_node.children - checked)
        checked.add(current_node)
        if end in to_check:
            end = [node for node in to_check if node == end][0]
            break
        elif current_node.get_depth() == 6:
            failed_to_find = True
            break
        print('.', end= ' ')
    
    if save_to_db:
        puzzle, created = (
            Puzzle.objects
            .get_or_create(
                start_movie_id=start.node_id, 
                end_movie_id=end.node_id,
            )
        )
        Solution.objects.get_or_create(puzzle=puzzle, solution=end.path_array([]))
    elif failed_to_find:
        print('Failed to find a solution in 6 or fewer steps.')
    else:
        print()
        end.pprint([])
        print(end.path_array([]))
