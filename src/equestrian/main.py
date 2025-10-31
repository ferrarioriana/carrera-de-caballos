import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from equestrian.game.engine import run_game

if __name__ == "__main__":
    run_game()
