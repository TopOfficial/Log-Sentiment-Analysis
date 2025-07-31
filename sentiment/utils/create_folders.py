import os


def create_folder_if_not_exists(directory):
    """
    Ensures a directory exists; creates it if it doesn't.

    :param directory: Path of the directory to check or create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")
    else:
        print(f"Directory already exists: {directory}")

def get_output_subdirectory(log_root_dir, log_subdir, output_dir):
    """
    Creates a subdirectory structure in the output directory that mirrors the structure of the logs.

    :param log_root_dir: Root directory of the logs.
    :param log_subdir: Subdirectory relative to the log root directory.
    :param output_dir: The root output directory where subdirectories will be created.
    :return: The full path of the subdirectory in the output directory.
    """
    # Get the relative path of the subdirectory from the log root
    relative_subdir = os.path.relpath(log_subdir, log_root_dir)

    # Create the corresponding subdirectory in the output folder
    output_subdir = os.path.join(output_dir, relative_subdir)
    create_folder_if_not_exists(output_subdir)

    return output_subdir