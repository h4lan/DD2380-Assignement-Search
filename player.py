#!/usr/bin/env python3
import sys
import math
import random

from fishing_game_core.game_tree import Node
from fishing_game_core.player_utils import PlayerController
from fishing_game_core.shared import ACTION_TO_STR


class PlayerControllerHuman(PlayerController):
    def player_loop(self):
        """
        Function that generates the loop of the game. In each iteration
        the human plays through the keyboard and send
        this to the game through the sender. Then it receives an
        update of the game through receiver, with this it computes the
        next movement.
        :return:
        """

        while True:
            # send message to game that you are ready
            msg = self.receiver()
            if msg["game_over"]:
                return


class PlayerControllerMinimax(PlayerController):

    def __init__(self):
        super(PlayerControllerMinimax, self).__init__()

    def player_loop(self):
        """
        Main loop for the minimax next move search.
        :return:
        """

        # Generate first message (Do not remove this line!)
        first_msg = self.receiver()

        while True:
            msg = self.receiver()

            # Create the root node of the game tree
            node = Node(message=msg, player=0)

            # Possible next moves: "stay", "left", "right", "up", "down"
            best_move = self.search_best_next_move(initial_tree_node=node)

            # Execute next action
            self.sender({"action": best_move, "search_time": None})

    def utility(self, node: Node):
        scores = node.state.get_player_scores()
        return scores[0] - scores[1] 

    def simple_eval_func(self, node : Node):
        scores = node.state.get_player_scores()
        return scores[0] - scores[1] 

    def eval_func_2(self, node : Node, threshold = 15):
        # TODO threshold should be a function
        max_distance = 19 + 20 # TODO fix magic number 
        hook_position = node.state.get_hook_positions()[0]
        fish_positions = node.state.get_fish_positions()
        fish_scores = node.state.get_fish_scores()

        eval = 0
        for fish_number in fish_positions:
            distance = abs(hook_position[0] - fish_positions[fish_number][0]) + abs(hook_position[1] -  fish_positions[fish_number][1])
            if distance < threshold:
                eval += fish_scores[fish_number] * (max_distance - distance)

        return eval

    def print_nodes(self, nodes : list, heuristic):
        str = "Possible next moves:\n"
        
        if nodes:
            for node in nodes:
                str += f"move={ACTION_TO_STR[node.move]}, heuristic={heuristic(node)}\n"

        print(str, file=sys.stderr)        

    def minimax(self, node : Node, player : int, remaining_depth, eval_func):
        """_summary_
        Minimax implementation with cut-off
        Args:
            node (_Node_): _description_
            player (_type_): _description_
            remaining_depth (_int_): _description_
        """

        # Initialize the children with compute_and_get_children()
        children = node.compute_and_get_children()

        if not children:
            # print("Termiial", file=sys.stderr)
            return (node, self.utility(node))
        elif remaining_depth == 0:
            # print("Cutoff", file=sys.stderr)
            return (node, eval_func(node))

        else:
            # self.print_nodes(children, eval_func)

            best_possible, best_value = None, None
            if player == 0: # MAX player
                best_value = float("inf")
                for child in children:
                    _, value = self.minimax(child, 1, remaining_depth-1, eval_func)
                    if best_possible == None or best_value < value:
                        best_possible, best_value = child, value
            
            else: # MIN player
                best_value = -float("inf")
                for child in children:
                    _, value = self.minimax(child, 0, remaining_depth-1, eval_func)
                    if best_possible == None or best_value > value:
                        best_possible, best_value = child, value
            
            return (best_possible, best_value)

    def search_best_next_move(self, initial_tree_node):
        """
        Use minimax (and extensions) to find best possible next move for player 0 (green boat)
        :param initial_tree_node: Initial game tree node
        :type initial_tree_node: game_tree.Node
            (see the Node class in game_tree.py for more information!)
        :return: either "stay", "left", "right", "up" or "down"
        :rtype: str
        """

        print("Computing...", file=sys.stderr)
        next_node, _ = self.minimax(initial_tree_node, 0, 2, self.eval_func_2) # we start off with depth only 2
        return ACTION_TO_STR[next_node.move]

        # random_move = random.randrange(5)
        # return ACTION_TO_STR[random_move]
