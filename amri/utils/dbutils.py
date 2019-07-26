import os
import pickle

from amri.utils.log_utils import log


class DbUtils:
    def __init__(self):
        self.db_path = os.path.abspath(__file__)
        self.db_path = self.db_path[:self.db_path.index('imr-framework') + len('imr-framework') + 1]
        self.db_path = os.path.join(self.db_path, 'database.p')

        try:
            log('\nReading database from disk...', endline='')
            db_file = open(self.db_path, 'rb')
            self.db = pickle.load(db_file)
            db_file.close()
        except FileNotFoundError:
            log('\nDatabase does not exist, returning new dict()')
            self.db = dict()

    def add_patient_to_database(self, patient_info_dict: dict):
        log('Adding patient to database...')
        uuid = patient_info_dict['uuid']
        self.db[uuid] = patient_info_dict

    def save_database(self):
        log('Saving database to disk...')
        db_file_writable = open(self.db_path, 'wb')
        pickle.dump(self.db, db_file_writable)
        db_file_writable.close()
