# Arcade — existing games, separate user permissions

Ctrl+Alt+Defeat **does not contain game engines**. It launches existing open-source terminal games installed by you, avoiding unauthorized redistribution and unnecessary Admin rights.

## Snake

1. Visit [baurst/rs_snake releases](https://github.com/baurst/rs_snake/releases) (MIT license).
2. Download the official Windows binary release, inspect the package and antivirus results, extract, and locate `rs_snake.exe`.
3. Place `rs_snake.exe` in `%USERPROFILE%\.ctrl_alt_defeat\arcade\` (create directory if necessary).
4. **Double-click `PlayArcade.cmd` as a normal user**, choose `1`, and play.

## Space Invaders

1. Visit [RetroArcade releases](https://github.com/fastrgv/RetroArcade/releases) (GPLv3) and download the official package.
2. Extract the archive using 7-Zip. Locate the Windows version of `cinv.exe` and keep its required runtime DLLs alongside it.
3. Copy the `bin\win` folder to `%USERPROFILE%\.ctrl_alt_defeat\arcade\invaders\bin\win\` preserving accompanying runtime files.
4. **Double-click `PlayArcade.cmd` as a normal user**, choose `2`, and play. The game opens in its own console session.

Some archives label the executable differently; verify the release contents if needed. Neither game was packaged here, so no claim of preinstalled gameplay is made.

## Why a separate launcher?

The main tool currently requests Administrator via UAC. Third-party games should never inherit elevated file-system privileges. `PlayArcade.cmd` starts directly, without elevation. If it is accidentally started from an elevated session, the arcade refuses to run. Do not launch game executables inside the Admin dashboard. A future version should make elevation per-task instead of per-application.

## License attribution

- Snake: [baurst/rs_snake](https://github.com/baurst/rs_snake), MIT.
- Space Invaders: [fastrgv/RetroArcade](https://github.com/fastrgv/RetroArcade), GPLv3. No binaries or GPL code are redistributed by this repository.
