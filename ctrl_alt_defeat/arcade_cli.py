"""Normal-user arcade launcher for separately installed, existing open-source games."""
from __future__ import annotations
import webbrowser
from .arcade import GAMES, game_dir, find_game, launch, is_admin


def main():
    print('CTRL + ALT + DEFEAT // ARCADE (STANDARD USER)')
    if is_admin():
        print('Refusing to run third-party games with Administrator rights.')
        input('Press Enter to close...')
        return 1
    print('Game directory:',game_dir())
    while True:
        for i,g in enumerate(GAMES,1):
            print(f'{i}: {g.name} [{"installed" if find_game(g) else "not installed"}]')
        print('0: Exit')
        response=input('Pick a game > ').strip()
        if response=='0':return 0
        if not response.isdigit() or not 1<=int(response)<=len(GAMES):
            print('Invalid selection.');continue
        game=GAMES[int(response)-1]
        try:
            proc=launch(game)
            print(f'Launched {game.name} (PID {proc.pid}) in its own console.')
        except FileNotFoundError:
            print('Game files not installed. Source:',game.project)
            print('Download the Windows binary from the project author, then place it in:')
            print(game_dir()/game.executable)
            if input('Open official releases in your browser? [y/N] > ').strip().lower()=='y':
                webbrowser.open(game.project)
        except (OSError,PermissionError) as exc:
            print('Launch failed:',exc)
    return 0

if __name__=='__main__':raise SystemExit(main())
