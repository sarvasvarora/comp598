from .database import Database


class HealthChecker():
    '''
    Class to perform health checking for all the online nodes.

    '''
    
    def __init__(self, database: Database):
        self.database = database

    def run(self):
        '''
        Run a health checker thread.
        '''
        pass