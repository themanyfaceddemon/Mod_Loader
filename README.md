# Mod Loader
![GitHub release (latest by date)](https://img.shields.io/github/v/release/themanyfaceddemon/Mod_Loader?label=release)

### Overview
`Mod Loader` - This tool is designed to ease the headache of managing modifications. It currently supports the following features:

- **Mod Conflict Detection**: Scans and identifies overwrites between mods to streamline conflict management.
- **Dependency-Aware Sorting**: Automatically sorts mods based on registered dependencies, ensuring they load in the correct order.
- **Easy Integration for Modders**: Simple setup that doesn’t require interaction with the main repository. Examples can be found [here](./metadata_example.xml) and in the [InternalLibrary directory](./Data/InternalLibrary) (except for `auto_pars` - there is no god there).

---

## Requirements
- [Python 3.12 or higher](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
---

## TODO:
- [ ] System of disabled/enabled parts of modifications depending on installed mods

## Installation

### 1. Install Python
Download and install [Python 3.12 or higher](https://www.python.org/downloads/) if it's not already installed on your system.

### 2. Install Git
Download and install [Git](https://git-scm.com/downloads) for repository management and code cloning.

### 3. Clone the Repository
Clone the repository using the command below:

```bash
git clone https://github.com/themanyfaceddemon/Mod_Loader.git
```
---

## Running the Application

### For Windows
Run the application using the `run_app.bat` file:
```bash
run_app.bat
```

### For Linux and macOS

Run the application using the `run_app.sh` file:
```bash
./run_app.sh
```

> [!NOTE]
> Make the script executable before running:
> ```bash
> chmod +x run_app.sh
> ```
---

## Support

If you encounter issues with `Mod Loader`, please open an issue in the repository or contact the developers for assistance.
---

## License
See the [LICENSE](./LICENSE) file for details.
