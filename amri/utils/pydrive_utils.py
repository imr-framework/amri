from pathlib import Path

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from amri.utils.log_utils import log


class PyDriveUtils:
    def __init__(self):
        path_pydrive_auth_settings = Path(__file__).parent / 'creds' / 'pydrive_auth_settings.yaml'
        self.gauth = GoogleAuth(settings_file=str(path_pydrive_auth_settings))
        self.gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(self.gauth)

    def get_crypt_key_if_exists(self):
        """
        Check if deg sitrep_drive_file.txt already exists on Google Drive (most likely from deg previous run). If it exists, check
        if only the crypt key was generated, scan.e. patient information was not uploaded. If yes, retrieve crypt key
        """
        crypt_key = None
        for l in self.sitrep.GetContentString().splitlines():
            if 'crypt_key' in l:
                crypt_key = l.split('crypt_key=')[1]
            if 'patient_info_dict' in l:
                raise Exception(
                    'Please delete the sitrep_drive_file.txt file on Google Drive and restart the procedure.')
        return False if crypt_key is None else crypt_key

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
            file_name = Path(file_name).parts[-1]
        log('Uploading {}...'.format(file_name), verbose=verbose)
        if child_of_folder is None:
            upload_file = self.drive.CreateFile({'title': file_name})
        else:
            upload_file = self.drive.CreateFile({'title': file_name, 'folderID': child_of_folder})
        upload_file.SetContentFile(file_path)
        upload_file.Upload()

    def search_for_files(self, filename, verbose=True):
        """Search for file in root of Google Drive."""
        query = 'title=\'{}\' and \'root\' in parents and trashed=false'.format(filename)
        files = self.drive.ListFile({'q': query}).GetList()
        return files

    def check_file_exists(self, filename: str, verbose: bool = True):
        """
        Return file if it already exists, else return False

        Parameters:
        -----------
        file_path : str
            Name of file to check if it already exists
        verbose : bool
            Boolean flag indicating log verbosity

        Returns:
        --------
        GoogleDriveFile if it exists, else False
        """

        log('Checking if {} exists...'.format(filename), verbose=verbose)
        files = self.search_for_files(filename=filename, verbose=verbose)
        if len(files) == 1:
            log('Found {}...'.format(filename), verbose=verbose)
            return files[0]
        elif len(files) == 0:
            return False
        else:
            raise Exception('Please delete the sitrep_drive_file.txt file on Google Drive and restart the procedure.')

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

    def get_file_contents_as_bytes(self, drive_file, verbose=True):
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
        log('Retrieving contents of {} as bytes...'.format(drive_file['title']), verbose=verbose)
        file_contents = bytes(drive_file.GetContentString(), 'utf-8')
        return file_contents

    def get_line_in_file(self, drive_file, condition, verbose=True):
        log('Checking for condition {} in {}...'.format(condition, drive_file), endline='\r', verbose=verbose)
        content_str = self.get_file_contents_as_string(drive_file=drive_file, verbose=False)
        for line in content_str.splitlines():
            if condition in line:
                log('Condition {} matched in {}...'.format(condition, drive_file['title']), verbose=verbose)
                return line
        return False
