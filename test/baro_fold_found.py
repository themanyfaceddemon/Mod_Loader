from pathlib import Path
import string
import os
import logging
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def is_system_directory(path):
    if os.name == 'nt':
        system_dirs = [
            Path("C:\\Windows"), 
            Path("C:\\Program Files"), 
            Path("C:\\Program Files (x86)")
        ]
        return path in system_dirs or path.is_relative_to(Path("C:\\Windows"))
    else:
        system_dirs = [
            Path("/usr"), 
            Path("/etc"), 
            Path("/bin"), 
            Path("/sbin")
        ]
        return path in system_dirs or path.is_relative_to(Path("/usr"))

def should_ignore_directory(entry, current_dir, game_name):
    ignored_directories = [
        "temp", "cache", "logs", "backup", "bin", "obj", "History", "httpcache", ".vscode", "venv", ".venv", ".nugget", ".git", "_cacache", "tmp"
    ]
    
    if entry.name.lower() in (dir_name.lower() for dir_name in ignored_directories):
        logger.info(f"Ignoring directory: {entry}")
        return True
    
    if current_dir.name.lower() == "steamapps" and entry.name.lower() == "workshop":
        logger.info(f"Ignoring directory: {entry} (in steamapps)")
        return True
    
    if current_dir.name.lower() == "common" and current_dir.parent.name.lower() == "steamapps":
        if entry.name.lower() != game_name:
            logger.info(f"Ignoring directory: {entry} (in steamapps\\common, does not match {game_name})")
            return True
    
    return False

def search_all_games_on_all_drives(game_name):
    game_name = game_name.lower()
    
    drives = [
        Path(drive) for drive in Path('/mnt').glob('*') if drive.is_dir()
    ] or [
        Path(f"{drive}:\\") for drive in string.ascii_uppercase if Path(f"{drive}:\\").exists()
    ]
    
    logger.info(f"Found drives: {len(drives)}")

    found_paths = []
    total_folders_checked = 0

    for drive in drives:
        logger.info(f"Processing drive: {drive}")
        dirs_to_visit = [drive]
        
        while dirs_to_visit:
            current_dir = dirs_to_visit.pop()
            logger.info(f"Processing directory: {current_dir}")
            total_folders_checked += 1
            
            if is_system_directory(current_dir):
                logger.info(f"Ignoring system folder: {current_dir}")
                continue
            
            try:
                for entry in current_dir.iterdir():
                    if entry.is_dir():
                        if should_ignore_directory(entry, current_dir, game_name):
                            continue

                        if entry.name.lower() == game_name:
                            logger.info(f"Match found: {entry}")
                            found_paths.append(entry)
                        else:
                            dirs_to_visit.append(entry)

            except PermissionError:
                logger.info(f"Access to directory {current_dir} denied. Continuing.")
            except Exception as e:
                logger.error(f"Error processing directory {current_dir}: {e}")

    return found_paths, total_folders_checked

start_time = time.time()
all_barotrauma_paths, total_checked = search_all_games_on_all_drives("Barotrauma")

elapsed_time = time.time() - start_time
logger.info(f"Total directories checked: {total_checked}")
logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")

if all_barotrauma_paths:
    logger.info("Found directories:")
    for path in all_barotrauma_paths:
        logger.info(path)
else:
    logger.info("Directories not found.")
