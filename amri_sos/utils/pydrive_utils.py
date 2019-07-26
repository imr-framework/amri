import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from amri_sos.utils import constants
from amri_sos.utils.log_utils import log

SECRETS_PATH = constants.SECRETS_PATH


class PyDriveUtils:
    SEQ_RESPONSES_FOLDER_ID = constants.SEQ_RESPONSES_FOLDER_ID

    def __init__(self):
        os.chdir(SECRETS_PATH)
        path_to_settings_yaml = SECRETS_PATH / 'settings.yaml'
        self.gauth = GoogleAuth(settings_file=path_to_settings_yaml)
        self.gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(self.gauth)

    def upload_file(self, file_path, child_of_folder=None, file_name=None, verbose=True):
        """
        Upload file to Google Drive

        Parameters:
        -----------
        file_path : str
            Path on disk of file to upload.
        child_of_folder : str
            Folder ID of the Google Drive folder into which this file will be uploaded.
        file_name : str
            Uploaded file name, if required to be different from file name on local disk.
        verbose : bool
            Boolean flag indicating log verbosity
        """
        if file_name is None:
            # Retrieve file name from path of file on disk
            file_name = os.path.split(file_path)[1]
        log('Uploading {}...'.format(file_name), verbose=verbose)
        if child_of_folder is None:
            upload_file = self.drive.CreateFile({'title': file_name})
        else:
            upload_file = self.drive.CreateFile({'title': file_name, 'parents': [{'id': child_of_folder}]})
        upload_file.SetContentFile(file_path)
        upload_file.Upload()

    def search_for_files(self, file_id):
        """Search for file in root of Google Drive."""
        query = f"'{file_id}' in parents"
        query = "'0B7vXgLdDs0yxfjRDTDlIbkVXNjNRQWN3dzJDZ2dJczZueEhJVl9JTXh5TVdXNzNNQXlPQTQ' in parents and trashed=false"
        files = self.drive.ListFile({'q': query}).GetList()
        return files

    def list_seq_responses(self):
        """
        List all seq file responses from
            /AMRI_SOS/AMRI_SOS_Form(File responses)/Step 5: Upload your .seq file (File responses)/
        Files are sorted in ascending order of date of creation.
        """

        query = '\'{}\' in parents and trashed=false'.format(self.SEQ_RESPONSES_FOLDER_ID)
        files = self.drive.ListFile({'q': query, 'orderBy': 'createdDate'}).GetList()
        return files

    def get_file_contents_as_string(self, drive_file, verbose=True):
        """
        Retrieve file contents as string

        Parameters:
        -----------
        file : pydrive.files.GoogleDriveFile
            GoogleDriveFile's contents to be retrieved as string
        verbose : bool
            Boolean flag indicating log verbosity

        Returns:
        --------
        file_contents : str
            file's contents as string
        """
        log('Retrieving contents of {} as string...'.format(drive_file['title']), verbose=verbose)
        file_contents = drive_file.GetContentString()
        return file_contents

    def get_file_contents_as_bytes(self, drive_file_id, verbose=True):
        """
        Retrieve file contents as bytes

        Parameters:
        -----------
        file : pydrive.files.GoogleDriveFile
            GoogleDriveFile's contents to be retrieved as bytes
        verbose : bool
            Boolean flag indicating log verbosity

        Returns:
        --------
        file_contents : bytes
            file's contents as bytes
        """
        drive_file = self.drive.CreateFile({'id': drive_file_id})
        drive_file.FetchMetadata()
        log('Retrieving contents of {} as bytes...'.format(drive_file['title']), verbose=verbose)
        file_contents = bytes(drive_file.GetContentString(), 'utf-8')
        return file_contents

    # def get_file_contents_as_bytes(self, drive_file, verbose=True):
    #     """
    #     Retrieve file contents as bytes
    #
    #     Parameters:
    #     -----------
    #     file : pydrive.files.GoogleDriveFile
    #         GoogleDriveFile's contents to be retrieved as bytes
    #     verbose : bool
    #         Boolean flag indicating log verbosity
    #
    #     Returns:
    #     --------
    #     file_contents : bytes
    #         file's contents as bytes
    #     """
    #     log('Retrieving contents of {} as bytes...'.format(drive_file['title']), verbose=verbose)
    #     file_contents = bytes(drive_file.GetContentString(), 'utf-8')
    #     return file_contents

    def get_line_in_file(self, drive_file, condition, verbose=True):
        log('Checking for condition {} in {}...'.format(condition, drive_file), endline='\r', verbose=verbose)
        content_str = self.get_file_contents_as_string(drive_file=drive_file, verbose=False)
        for line in content_str.splitlines():
            if condition in line:
                log('Condition {} matched in {}...'.format(condition, drive_file['title']), verbose=verbose)
                return line
        return False
