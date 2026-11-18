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
        self.max_depth = 3 # change this to test different depths

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

    def score_distance_eval_func(self, node : Node):
        def move_distance(t1, t2):
            """_summary_

            Args:
                t1 (_type_): _description_
                t2 (_type_): _description_

            Returns:
                _type_: _description_
            """
            y_dist = abs(t1[1] - t2[1])
            x_dist = abs(t1[0] - t2[0])
            wrap_around_x_dist = 20 - max(t1[0], t2[0]) + min(t1[0], t2[0]) 

            return min(x_dist, wrap_around_x_dist) + y_dist
        
        scores = node.state.get_player_scores()
        hook_positions = node.state.get_hook_positions()
        fish_positions = node.state.get_fish_positions()
        fish_scores = node.state.get_fish_scores()
        caught_fish = node.state.get_caught()

        # Computing distance between the fish and the players' hooks
        max_fish_distances = (0,0)
        min_fish_distances = (float("inf"), float("inf"))
        fish_distances = {}
        for fish_number in fish_positions:
            dist = (move_distance(hook_positions[0], fish_positions[fish_number]),
                    move_distance(hook_positions[1], fish_positions[fish_number]))
            
            fish_distances[fish_number] = dist
            max_fish_distances = (max(max_fish_distances[0], dist[0]), max(max_fish_distances[1], dist[1]))
            min_fish_distances = (min(min_fish_distances[0], dist[0]), min(min_fish_distances[1], dist[1]))

        # Take player scores in account through the score difference
        eval = scores[0] - scores[1] # score weight = 1

        # Take fish positions in account through their distance from the hook
        for fish_number in fish_distances:
            dist = fish_distances[fish_number]
            # Fish caught be the other player should not count
            # Small value to break the tie: even if the last fish is caught, the cases where MAX is closer to it are better
            eval += (fish_scores[fish_number] if fish_number != caught_fish[1] else 0.001) / (dist[0] + 1)
            eval += -(fish_scores[fish_number] if fish_number != caught_fish[0] else 0.001) / (dist[1] + 1) 
        
        return eval

    def print_values(self, values):
        str = "Possible next moves:\n"
        
        if values:
            for move, value in enumerate(values):
                str += f"(move={ACTION_TO_STR[move]}, value={value}) "

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
            return (node, self.utility(node))

        # Cutoff
        if remaining_depth == 0:
            return (node, eval_func(node))

        else:
            children_values = []

            print(f"Depth = {self.max_depth - remaining_depth}", file = open("log.txt", "a"))

            best_possible, best_value = None, None
            if player == 0: # MAX player
                best_value = -float("inf")
                for child in children:
                    _, value = self.minimax(child, 1, remaining_depth-1, eval_func)

                    if best_possible == None or best_value < value:
                        best_possible, best_value = child, value

            
            else: # MIN player
                best_value = float("inf")
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

        next_node, _ = self.minimax(initial_tree_node, 0, self.max_depth, self.score_distance_eval_func) # we start off with depth only 2
        return ACTION_TO_STR[next_node.move]
