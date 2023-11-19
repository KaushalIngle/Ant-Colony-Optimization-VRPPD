import math
import sys
import os.path

number_of_ants = 5
number_of_iterations = 50

#factor for pheromone evaporation
pheromone_evaporation = 0.1

#factor for pheromone intensity
alpha = 1

#factor for distance priority (exponential)
beta = 2

# get data file path from command line
data_file = sys.argv[1]
load_data = []

# check if data file exists
if not os.path.isfile(data_file):
    print("File path {} does not exist. Exiting...".format(data_file))
    sys.exit()

# read data file into load_data as a list of tuples (loadnumber, (pickup_x, pickup_y), (dropoff_x, dropoff_y)
with open(data_file, 'r') as f:
    line = f.readline()
    while line:
        if line.startswith("loadNumber"):
            line = f.readline()
            continue
        line_split = line.split(" ")
        loadnumber = int(line_split[0])
        pickup_coords = line_split[1][1:-1].split(",")
        pickup_x = float(pickup_coords[0])
        pickup_y = float(pickup_coords[1])
        dropoff_coords = line_split[2][1:-2].split(",")
        dropoff_x = float(dropoff_coords[0])
        dropoff_y = float(dropoff_coords[1])
        load_data.append((loadnumber, (pickup_x, pickup_y), (dropoff_x, dropoff_y)))
        line = f.readline()

# initialize variables
max_shift_time = 12*60
total_loads = len(load_data)
delivery_distance = [0 for x in range(total_loads)]
distance_matrix = [[0 for x in range(total_loads+1)] for y in range(total_loads+1)] 
pheromone_matrix = [[0 for x in range(total_loads+1)] for y in range(total_loads+1)]

#populate delivery distance array
for i in range(total_loads):
    delivery_distance[i] = math.sqrt((load_data[i][1][0] - load_data[i][2][0])**2 + (load_data[i][1][1] - load_data[i][2][1])**2)

# populate distance matrix
for i in range(total_loads+1):
    for j in range(total_loads+1):
        # distance from depot to depot is 0
        if i == j:
            distance_matrix[i][j] = 0
        # distance from depot to load pickup
        elif i == 0:
            distance_matrix[i][j] = math.sqrt((load_data[j-1][1][0])**2 + (load_data[j-1][1][1])**2)
        #distance from load dropoff to depot
        elif j == 0:
            distance_matrix[i][j] = math.sqrt((load_data[i-1][2][0])**2 + (load_data[i-1][2][1])**2)
        #distance from load dropoff to next load pickup
        else:
            distance_matrix[i][j] = math.sqrt((load_data[i-1][2][0] - load_data[j-1][1][0])**2 + (load_data[i-1][2][1] - load_data[j-1][1][1])**2)

# populate pheromone matrix
for i in range(total_loads+1):
    for j in range(total_loads+1):
        if i == j:
            # pheromone from node to itself is 0
            pheromone_matrix[i][j] = 0
        else:
            pheromone_matrix[i][j] = 1

# calculate fitness for solution
def calculate_fitness(solution):
    """
    Calculate fitness of a solution based on total distance travelled by all vehicles
    :param solution: list of lists, each list represents a vehicle's path
    :return: fitness value of the solution ie 1/total_distance
    """
    no_of_drivers = len(solution)
    total_distance = 0
    for i in range(len(solution)):
        for j in range(len(solution[i])):
            if j == 0:
                total_distance += distance_matrix[0][solution[i][j]] + delivery_distance[solution[i][j]-1]
            else:
                total_distance += distance_matrix[solution[i][j-1]][solution[i][j]] + delivery_distance[solution[i][j]-1]
        total_distance += distance_matrix[solution[i][len(solution[i])-1]][0]
        no_of_drivers += 1
    total_cost = total_distance +(500 * no_of_drivers)
    return 1.0/total_cost

# initialize ant solutions
costliest_solution = [[x] for x in range(total_loads+1)]
ant_solutions = []
ant_solutions.append(costliest_solution)

# ant colony optimization
for iteration in range(number_of_iterations):
    # generate solutions
    for _ in range(number_of_ants):
        solution = []
        vehicle_distance = 0
        current_node = 0
        vehicle_path = []
        remaining_loads = [x for x in range(1, total_loads+1)]
        while len(remaining_loads) > 0:
            next_node = 0
            max_probability = 0
            possible_delivery = False
            for j in range(len(remaining_loads)):
                # check if vehicle can deliver load
                if vehicle_distance + distance_matrix[current_node][remaining_loads[j]] + delivery_distance[remaining_loads[j]-1] + distance_matrix[remaining_loads[j]][0] > max_shift_time:
                    continue
                probability = (pheromone_matrix[current_node][remaining_loads[j]]**alpha) * ((1/distance_matrix[current_node][remaining_loads[j]])**beta)
                possible_delivery = True
                # check if probability is greater than max_probability
                if probability > max_probability:
                    max_probability = probability
                    next_node = remaining_loads[j]
            # if vehicle cannot deliver any load, return to depot
            if not possible_delivery:
                solution.append(vehicle_path)
                vehicle_distance = 0
                current_node = 0
                vehicle_path = []
                continue
            vehicle_distance += distance_matrix[current_node][next_node] + delivery_distance[next_node-1]
            vehicle_path.append(next_node)
            remaining_loads.remove(next_node)
            current_node = next_node
        
        solution.append(vehicle_path)
        
        # update pheromone matrix
        fitness = calculate_fitness(solution)
        for i in range(len(solution)):
            for j in range(len(solution[i])+1):
                if j == 0:
                    pheromone_matrix[0][solution[i][j]] = (1-pheromone_evaporation)*pheromone_matrix[0][solution[i][j]] + fitness
                elif j == len(solution[i]):
                    pheromone_matrix[solution[i][j-1]][0] = (1-pheromone_evaporation)*pheromone_matrix[solution[i][j-1]][0] + fitness
                else:
                    pheromone_matrix[solution[i][j-1]][solution[i][j]] = (1-pheromone_evaporation)*pheromone_matrix[solution[i][j-1]][solution[i][j]] + fitness
        ant_solutions.append(solution)

    # evaporation of pheromone matrix
    for i in range(total_loads+1):
        for j in range(total_loads+1):
            pheromone_matrix[i][j] = (1-pheromone_evaporation)*pheromone_matrix[i][j]
    

# find best solution
best_solution = max(ant_solutions, key=calculate_fitness)

# print best solution
for i in best_solution:
    sys.stdout.write("[")
    for j in i:
        if j == i[len(i)-1]:
            sys.stdout.write(str(j))
        else:
            sys.stdout.write(str(j)+",")
    sys.stdout.write("]")
    sys.stdout.flush()
    sys.stdout.write("\n")