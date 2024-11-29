from pathlib import Path


def read_loc_file(file_path):
    loc_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                loc_dict[key.strip()] = value.strip()

    return loc_dict


def normalize_loc_file(file_path):
    loc_dict = read_loc_file(file_path)
    sorted_loc_dict = dict(sorted(loc_dict.items()))
    with open(file_path, "w", encoding="utf-8") as f:
        for key, value in sorted_loc_dict.items():
            f.write(f"{key} = {value}\n")


def normalize_loc_files_in_directory(directory_path):
    directory = Path(directory_path)

    for loc_file in directory.rglob("*.loc"):
        print(f"Normalize the file: {loc_file}")
        normalize_loc_file(loc_file)

    print("Normalization is complete.")


input_directory = "Data/localization"
normalize_loc_files_in_directory(input_directory)
