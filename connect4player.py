"""
This Connect Four player uses minimax to score the
"""
__author__ = "Lucas Gover" 
__license__ = "UPS"
__date__ = "February 2022"

import random
import threading

class ComputerPlayer:

    def __init__(self, id, difficulty_level):
        self.id = id
        self.difficulty_level = difficulty_level

    def pick_move(self, rack):

        #make an imaginary list equivalent of the rack, in which the progam can use to test possible moves
        imaginary_board = [list(row) for row in rack]

        #makes a list of scores, with scores[collumn] storing the score if ComputerPlayer plays in that collumn
        scores = list()

        #tries out every possible move
        for i in range(len(rack)):

            #If collumn is full, don't even try it
            if not (imaginary_board[i][-1] == 0):
                scores.append(None)
                continue
            
            #find the top open spot in the collumn(where the piece will drop to)
            top_open_spot = self._find_top_spot_open(rack,i)
            
            imaginary_board[i][top_open_spot] = self.id # plays in collumn i on the imaginary board

            #uses minimax to score this new board
            score = self._minimax_with_alpha_beta_pruning(self._flip_player(self.id),imaginary_board,self.difficulty_level - 1,-100000000,100000000) * -1
            #print("[{}]: ".format(i+1) + str(score)) # <- use if you want to see what minimax scores each possible move

            scores.append(score) 
            imaginary_board[i][top_open_spot] = 0 # reset board
        
        best_collumns = [] # stores all the collumns that tie for best score
        best_score = -100000000

        # finds all collumns that tie for the best score(usually just one) and randomly selects one
        # probably unneccessary, but more interesting to play against
        for i in range(len(scores)):
            if(scores[i] == None):
                continue
            if(best_score < scores[i]):
                best_score = scores[i]
                best_collumns = []
            if(best_score == scores[i]):
                best_collumns.append(i)
        
        return random.choice(best_collumns) # out of the best collumns, choses one

    #returns the score as the current_id_player
    def _minimax(self,id, board,depth):
        curr_score = self._eval_function(id,board)

        #check if at base case
        if depth <= 0:
            return curr_score
        
        #Check if Win or Tie State is reached
        if(curr_score > 100000):
            return curr_score - 1
        if(curr_score < -100000):
            return curr_score + 1
        if self._is_tie(board):
            return 0

        #Look through each possible spot and select best one
        best_score = -100000000
        for i in range(len(board)):

            #if collumn isn't open, don't check it
            if not (board[i][-1] == 0):
                continue

            #find top open spot
            row = self._find_top_spot_open(board,i)
            board[i][row] = id

            #use minimax to get score
            score = self._minimax(self._flip_player(id),board,depth-1) * -1
            best_score = max(score,best_score)

            board[i][row] = 0 #reset board
        
        #don't be mean
        if(best_score > 100000):
            return best_score - 1
        if(best_score < -100000):
            return best_score + 1

        #return the Score of best position
        return best_score

    def _minimax_with_alpha_beta_pruning(self,id, board,depth,alpha, beta):

        curr_score = self._eval_function(id,board)

        #check if at base case
        if depth <= 0:
            return curr_score
        
        #Check if Win or Tie State is reached
        if(curr_score > 100000):
            return curr_score - 1 #subtracts 1 to deprioritize further away guaranteed wins
        if(curr_score < -100000):
            return curr_score + 1 #adds 1 to deprioritize further away guaranteed wins
        if self._is_tie(board):
            return 0

        #Look through each possible spot and select best one
        best_score = -100000000
        for i in range(len(board)):

            #if collumn isn't open, don't check it
            if not (board[i][-1] == 0):
                continue

            #find top open spot
            row = self._find_top_spot_open(board,i)
            board[i][row] = id # sets the imaginary board

            #runs minimax to evaluate score
            score = self._minimax_with_alpha_beta_pruning(self._flip_player(id),board,depth-1, -1 * beta, -1 * alpha) * -1

            best_score = max(score,best_score)

            alpha = max(alpha,best_score) 
            board[i][row] = 0

            #doesn't check 
            if alpha >= beta: # all further nodes are guaranteed to be worse, no need to check them
                break
        
        #don't be mean
        if(best_score > 100000):
            return best_score - 1
        if(best_score < -100000):
            return best_score + 1

        #return the Score of best position
        return best_score

    
    #evaluates and scores the board
    def _eval_function(self,id,rack):
        score = 0
        
        #up and down
        for i in range(len(rack)):
            for j in range(len(rack[i]) - 3):
                pos = [(i,j), (i,j+1), (i,j+2), (i,j+3)]
                score += self._score_list(id,rack,pos)
        #sideways
        for i in range(len(rack) - 3):
            for j in range(len(rack[i])):
                pos = [(i,j), (i+1,j), (i+2,j), (i+3,j)]
                score += self._score_list(id,rack,pos)
        #diagonal North east
        for i in range(len(rack) - 3):
            for j in range(len(rack[i]) - 3):
                pos = pos = [(i,j),(i+1,j+1), (i+2,j+2), (i+3,j+3)]
                score += self._score_list(id,rack,pos)

        #diagonal North West
        for i in range(len(rack) - 3):
            for j in range(len(rack[i]) - 3):
                pos = [(i,j+3),(i+1,j+2), (i+2,j+1), (i+3,j)]
                score += self._score_list(id,rack,pos)
        
        #if win, simplify score so further away wins are deprioritized
        if score > 100000: 
            return 10000000
        #if loss, simplify score so further away wins are deprioritized
        if score < -100000:
            return -10000000
        #otherwise return score
        return score

    #scores a set of 4 spots on the board
    def _score_list(self,id,rack,positions):
        assert len(positions) == 4

        num_One = 0 # number of player 1 pieces in this set of four spots
        num_Two = 0 # number of player 2 pieces in this set of four spots

        #count number of ones and Twos
        for pos in positions:
            if(rack[pos[0]][pos[1]] == 1):
                num_One += 1
            if(rack[pos[0]][pos[1]] == 2):
                num_Two += 1
        
        #Check if this is a set of 4 that could still win
        if (num_Two > 0) and (num_One > 0):
            return 0
        if (num_Two == 0) and (num_One == 0):
            return 0

        #Check which player has pieces in this row has more
        num_two_higher = num_Two > num_One


        score = max(num_One,num_Two) #
        winning_id_is_id = (num_two_higher and (id == 2)) or ((not num_two_higher) and (id == 1))
        
        #gives out exponentially better scores based on how many tiles are in each board
        if score == 1:
            return 1 * (1 if winning_id_is_id else -1)
        if score == 2:
            return 10 * (1 if winning_id_is_id else -1)
        if score == 3:
            return 100 * (1 if winning_id_is_id else -1)
        if score == 4:
            return 10000000 * (1 if winning_id_is_id else -1)

    #checks for a tie game
    def _is_tie(self, board):
        for collumn in board:
            if collumn[-1] == 0:
                return False
        return True

    #changes the player id
    def _flip_player(self,id):
        return 3 - id
    
    #finds the top open spot in a given collumn
    def _find_top_spot_open(self,board, collumn):
        for i in range(len(board[collumn])):
            if(board[collumn][i] == 0):
                return i
        raise Exception("Collumn Full")
