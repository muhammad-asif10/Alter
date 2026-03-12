# Alter Desktop

## Run

From the repository root:

```bash
python desktop/main.py
```

## Build (.exe)

Build with the committed PyInstaller spec (windowed app preset):

```bash
pyinstaller Alter.spec
```

Output executable:

- `dist/Alter.exe`

## Notes

- Main entrypoint: `desktop/main.py`
- App package root: `desktop/alter_app/`
- If dependencies change, reinstall from `requirements.txt` before building.

## Project Docs

- Contributing guide: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- License: `LICENSE`
# Alter
