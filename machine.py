import random
from itertools import combinations, chain, product
from shapely.geometry import LineString, Point, Polygon
import copy

from typing import List, Tuple

import time

class MACHINE():
    """
        [ MACHINE ]
        MinMax Algorithm을 통해 수를 선택하는 객체.
        - 모든 Machine Turn마다 변수들이 업데이트 됨

        ** To Do **
        MinMax Algorithm을 이용하여 최적의 수를 찾는 알고리즘 생성
           - class 내에 함수를 추가할 수 있음
           - 최종 결과는 find_best_selection을 통해 Line 형태로 도출
               * Line: [(x1, y1), (x2, y2)] -> MACHINE class에서는 x값이 작은 점이 항상 왼쪽에 위치할 필요는 없음 (System이 organize 함)
    """
    def __init__(self, score=[0, 0], drawn_lines=[], whole_lines=[], whole_points=[], location=[]):
        self.id = "MACHINE"
        self.score = [0, 0] # USER, MACHINE
        self.drawn_lines = [] # Drawn Lines
        self.drawn_lines_copy = [] # for find_best_selection
        self.is_opponent_fooled_flag = True
        self.board_size = 7 # 7 x 7 Matrix
        self.num_dots = 0
        self.whole_points = []
        self.location = []
        self.triangles = [] # [(a, b), (c, d), (e, f)]

    def find_best_selection(self):
        self.drawn_lines_copy = copy.deepcopy(self.drawn_lines)

        fooling_triangles = self.return_fooling_triangles()

        if self.is_opponent_fooled(fooling_triangles) and self.is_opponent_fooled_flag:
            self.is_opponent_fooled_flag = True
        else:
            self.is_opponent_fooled_flag = False

        print("self.is_opponent_fooled_flag", self.is_opponent_fooled_flag)
        
        # 1점
        #   낚시 인지 확인

        print("FIND START")
        
        # 2점 얻을 수 있는 액션 있는지 확인, 있으면 line 반환
        if (line := self.check_get2point()) != None:
            print("choice : "+str(line))
            return line
        # 1점 얻을 수 있는 액션 있는지 확인, 있으면 낚시 상황 있는지 확인
        elif (line := self.check_get1point()) != None:
            print("choice : "+str(line))
            return line
        # 상대방이 낚시에 당하면 낚시 시도
        elif self.is_opponent_fooled_flag and (line := self.get_candidate_fooling_triangles(fooling_triangles)) != None:
            print("choice : "+str(line))
            return line
        elif (line := self.countNoScoreActions()) != None:
            self.drawn_lines_copy.append(line)
            print("HOW MANY NO SCORE ACTIONS AFTER CHOICE")
            temp = self.countNoScoreActions()
            print("END")
            print("choice : "+str(line))
            self.drawn_lines_copy.remove(line)
            return line
        else:
            available = [[point1, point2] for (point1, point2) in list(combinations(self.whole_points, 2)) if self.check_availability([point1, point2])]
            return random.choice(available)
        
    def organize_points(self, point_list):
        point_list.sort(key=lambda x: (x[0], x[1]))
        return point_list

    def check_availability(self, line):
        line_string = LineString(line)

        # Must be one of the whole points
        condition1 = (line[0] in self.whole_points) and (line[1] in self.whole_points)
        
        # Must not skip a dot
        condition2 = True
        for point in self.whole_points:
            if point==line[0] or point==line[1]:
                continue
            else:
                if bool(line_string.intersection(Point(point))):
                    condition2 = False

        # Must not cross another line
        condition3 = True
        for l in self.drawn_lines_copy:
            if len(list(set([line[0], line[1], l[0], l[1]]))) == 3:
                continue
            elif bool(line_string.intersection(LineString(l))):
                condition3 = False

        # Must be a new line
        condition4 = (line not in self.drawn_lines_copy)

        if condition1 and condition2 and condition3 and condition4:
            return True
        else:
            return False   
        



####################################################### 신예찬 #######################################################
    
    def check_get2point(self):
        start = time.time()
        candidate = []
        count = 0
        target_points = list(set(self.return_dots_from_lines(self.drawn_lines_copy)))
        for (point1, point2) in list(combinations(target_points, 2)):
            if self.check_availability([point1, point2]): # 이 선이 그릴 수 있는 선인지?
                newLine = self.organize_points([point1, point2])
                if self.check_triangleCount(newLine) == 2:
                    candidate.append(newLine)
                    print("get2point : " + str(newLine))
        if candidate:
             return random.choice(candidate)

        
            
        
    def check_get1point(self):
        # 상대방이 방금 그은 선분만 확인 -> 이 선분이 아닌 다른 선분들은 확인할 필요가 없지 않을까? -> 아니었음
        # 그 선분으로 점수가 나는 상황 -> 내가 낚시에 걸리는 상황인지 확인, 아니라면 점수 획득

        candidate = []
        
        # 모든 선분에 대해 점수 낼 수 있는 선분이 있는지 판단
        for previousLine in self.drawn_lines_copy:

            # 한 선분의 양 끝 점에 연결된 다른 선분들 찾기
            point1 = previousLine[0]
            point2 = previousLine[1]
            point1_connected = [] 
            point2_connected = []
            for l in self.drawn_lines_copy:
                if l==previousLine: # 자기 자신 제외
                    continue
                if point1 in l:
                    point1_connected.append(l)
                if point2 in l:
                    point2_connected.append(l)

            # 두 점 각각에 대해 연결된 선분과 함께 만들어지는 점수가 있는지 판단
            if point1_connected:
                for l in point1_connected:
                    p = l[0] if l[0] != point1 else l[1]
                    thirdLine = self.organize_points([p,point2]) # 
                    if self.check_availability(thirdLine):
                        triangle = self.organize_points(list(set(chain(*[previousLine, l, thirdLine]))))
                        if len(triangle) != 3 or triangle in self.triangles: # 삼각형이 아니거나 이미 있는 삼각형인 경우는 패스
                            continue

                        empty = True
                        for point in self.whole_points: # 만들어진 삼각형 내부에 점이 있는지 판단
                            if point in triangle:
                                continue
                            if bool(Polygon(triangle).intersection(Point(point))):
                                empty = False
                        if empty:
                            # 낚시 상황인지 판단하고 아닐경우에, candidate에 없는 원소이면 추가
                            if thirdLine not in candidate:
                                candidate.append(thirdLine)
            # 두번째 점
            if point2_connected:
                for l in point2_connected:
                    p = l[0] if l[0] != point2 else l[1]
                    thirdLine = self.organize_points([p,point1])
                    if self.check_availability(thirdLine):
                        triangle = self.organize_points(list(set(chain(*[previousLine, l, thirdLine]))))
                        if len(triangle) != 3 or triangle in self.triangles: # 삼각형이 아니거나 이미 있는 삼각형인 경우는 패스
                            continue

                        empty = True
                        for point in self.whole_points: # 만들어진 삼각형 내부에 점이 있는지 판단
                            if point in triangle:
                                continue
                            if bool(Polygon(triangle).intersection(Point(point))):
                                empty = False
                        if empty:
                            # 낚시 상황인지 판단하고 아닐경우에, candidate에 없는 원소이면 추가
                            if thirdLine not in candidate:
                                print("get1point : "+ str(thirdLine))
                                candidate.append(thirdLine)
        
        # 후보가 있으면, 낚시 인지 확인해야함
        if candidate:
            candidate_final = []
            result = self.return_fooling_triangles()

            for line in candidate:
                
                for triangle_dot, triangle_lines in result["fooling_triangles"]:
                    line_dots = set(self.return_dots_from_lines([line]))
                    triangle_dots = set(self.return_dots_from_lines(triangle_lines))

                    if line_dots == triangle_dots.intersection(line_dots):
                        print("fooling line : "+ str(line))
                        break
                else:
                    candidate_final.append(line)

            if candidate_final:
                return candidate_final[0]



    def countNoScoreActions(self):
        candidate = []
        count = 0
        for (point1, point2) in list(combinations(self.whole_points, 2)):
            if self.check_availability([point1, point2]): # 이 선이 그릴 수 있는 선인지?
                newLine = self.organize_points([point1, point2])
                self.drawn_lines_copy.append(newLine) # 그릴 수 있는 선이라면 그렸다고 가정하고 리스트에 추가
                if self.check_get1point() == None and self.check_get2point() == None: # 그린 상황에서 점수가 발생하는지 확인
                    candidate.append(newLine)
                    count += 1
                    print(point1, point2)
                self.drawn_lines_copy.remove(newLine) # 넣었던 선 다시 삭제
        print("NoScoreAction : " + str(count))
        if candidate:
            return random.choice(candidate)


    def check_triangleCount(self, line):
        get_score_count = 0

        point1 = line[0]
        point2 = line[1]

        point1_connected = [] # 방금 그은 선의 두 점에 이미 그어진 line을 담는 배열
        point2_connected = []

        for l in self.drawn_lines_copy:
            if l==line: # 자기 자신 제외
                continue
            if point1 in l:
                point1_connected.append(l)
            if point2 in l:
                point2_connected.append(l)

        if point1_connected and point2_connected: # 최소한 2점 모두 다른 선분과 연결되어 있어야 함
            for line1, line2 in product(point1_connected, point2_connected):
                
                # Check if it is a triangle & Skip the triangle has occupied
                triangle = self.organize_points(list(set(chain(*[line, line1, line2]))))
                if len(triangle) != 3 or triangle in self.triangles: # 삼각형이 아니거나 이미 있는 삼각형인 경우는 패스
                    continue
                
                get_score = True
                for point in self.whole_points: # 만들어진 삼각형 내부에 점이 있는지 판단
                    if point in triangle:
                        continue
                    if bool(Polygon(triangle).intersection(Point(point))):
                        get_score = False
                if get_score:
                    get_score_count += 1
        
        return get_score_count

####################################################### 신예찬 #######################################################












####################################################### 이원준 #######################################################

    #5.외부와 연결되지 않은 두 선분 찾는 함수
    def find_unconnected_lines(self):
        """
        input: 

        output: 두 연결되지 않은 선분 line1 line2, 연결되지 않은 선분이 없으면 None
        """
        for line1 in self.drawn_lines:
            for line2 in self.drawn_lines:
                if line1 != line2 and not self.is_line_connected(line1, line2) and not self.has_point_inside(line1, line2):
                    return line1, line2
        return None

    #선분의 끝점이 맞닿아 있는지 확인하는 함수
    def is_line_connected(self, line1, line2):
        """
        input: line1, line2

        output: 선분이 끝점을 공유하면 True, 그렇지 않으면 False
        """
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        # Check if the lines share an endpoint
        if (x1, y1) == (x3, y3) or (x1, y1) == (x4, y4) or (x2, y2) == (x3, y3) or (x2, y2) == (x4, y4):
            return True

        # Check if the lines overlap
        line1 = LineString([line1[0], line1[1]])
        line2 = LineString([line2[0], line2[1]])
        return line1.intersects(line2)
    
    #내부에 점이 있는지 확인하는 함수
    def has_point_inside(self, line1, line2):
        """
        input: line1, line2

        output: 선분으로 만들어진 다각형 내에 어떤 점이라도 있으면 True, 그렇지 않으면 False
        """
        # Extract coordinates of the four points
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Check if any whole_points, excluding the points of line1 and line2, are inside the polygon
        points_to_check = set(self.whole_points) - set([line1[0], line1[1], line2[0], line2[1]])
        inside_polygon = any(polygon.contains(Point(point)) or
                            Point(point).within(LineString([(x2, y2), (x3, y3)])) or
                            Point(point).within(LineString([(x4, y4), (x1, y1)])) or
                            Point(point).within(LineString([(x1, y1), (x3, y3)])) or
                            Point(point).within(LineString([(x2, y2), (x4, y4)])) for point in points_to_check)

        # If any whole_points are inside, return True; otherwise, return False
        return inside_polygon


    #6.외부와 연결되지 않은 두 선분으로 만들 수 있는 선분의 개수 구하는 함수
    def count_possible_lines(self, line1, line2):
        """
        input: line1, line2

        output: 주어진 선분들 사이에 그을 수 있는 선분의 수
        """
        count = 0
        for point1 in line1:
            for point2 in line2:
                if point1 != point2 and self.check_availability([point1, point2]):
                    count += 1
        if self.is_diagonal_blocked(line1, line2):
            count -= 1
        return count

    #대각선이 겹치는지 확인하는 함수
    def is_diagonal_blocked(self, line1, line2):
        """
        input: line1, line2

        output: 두 선분으로 만들어진 대각선이 교차하면 True, 그렇지 않으면 False
        """
        diagonal1 = LineString([line1[0], line2[0]])
        diagonal2 = LineString([line1[1], line2[1]])
        diagonal3 = LineString([line1[0], line2[1]])
        diagonal4 = LineString([line1[1], line2[0]])
        return diagonal1.crosses(diagonal2) or diagonal3.crosses(diagonal4)
    
####################################################### 이원준 #######################################################














####################################################### 김수환 #######################################################

    def is_triangle(self, lines: List[Tuple[int, int]]) -> bool:
        """
        Line: [(x1, y1), (x2, y2)]으로 이루어진 리스트를 받아서 삼각형인지 반환하는 함수입니다.

        input : lines
            lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]] 형식의 List[List[Tuple[int, int], ...]] 

        output : is_triangle
            is_triangle : True, False
        """
        # Line: [(x1, y1), (x2, y2)]
        # lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]]

        dots = self.return_dots_from_lines(lines)

        if len(dots) == 3: # if is triangle
            return True
        else:
            return False
        
    def is_occupied(self, lines: List[Tuple[int, int]]) -> bool:
        """
        Line: [(x1, y1), (x2, y2)]으로 이루어진 리스트를 받아서 이미 차지된 삼각형인지 반환하는 함수입니다.

        input : lines
            lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]] 형식의 List[List[Tuple[int, int], ...]] 
        output : is_occupied
            is_occupied : True, False
        """
        # Line: [(x1, y1), (x2, y2)]
        # lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]]

        triangle = self.return_dots_from_lines(lines)

        if triangle in self.triangles: # if is triangle
            return True
        else:
            return False
        
    def return_dots_from_lines(self, lines: List[Tuple[int, int]]) -> List[Tuple[int]]:
        """
        Line: [(x1, y1), (x2, y2)]을 리스트를 받아서 포함된 모든 점의 집합을 반환하는 함수입니다.

        input : lines
            lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]] 형식의 List[Line, ...]

        output : organized_dots
            organized_dots: List[dot]
        """
        organized_dots = self.organize_points(list(set(chain(*[*lines]))))
        return organized_dots
        
    

    # return if line makes triangles (includes no-score triangle)
    def return_triangles(self) -> List[List[List[Tuple[int, int]]]]:
        """
        현재 map에 존재하는 모든 삼각형을 반환하는 함수입니다. 점수로 인정되지 않는 삼각형도 모두 반환합니다.
        
        input : -

        output : triangles
             triangles: List[List[Line, Line, Line], ...]
        """
        triangles = []
        line_combinations = combinations(self.drawn_lines_copy, 3)

        # for all 3-line combinations (nC3)
        for line_combination in line_combinations:
            
            # if 3-line combination is triangle and not occupied
            if self.is_triangle(line_combination) and not self.is_occupied(line_combination):
                triangles.append(line_combination)

        return triangles
    

    def is_fooling_triangle(self, triangle: List[Tuple[int, int]]):
        """
        삼각형을 입력받아 낚시 삼각형인지와, 해당 삼각형이 포함하는 선분, 점을 반환합니다.

        input : triangle
            triangle: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]] 형식의 List[Line, Line, Line]

        output : [is_fooling_triangle, inside_dots, inside_lines]
            is_fooling_triangle: 낚시 삼각형인지 아닌지 True, False 반환
            inside_dots: 삼각형이 포함하는 모든 점 반환
            inside_lines: 삼각형이 포함하는 모든 선분 반환
        """
        # Line: [(x1, y1), (x2, y2)]
        # triangle: [Line, Line, Line]

        # all dots from all lines
        # dots = list(set(chain(*[triangle[0], triangle[1], triangle[2]])))

        # 삼각형 내부에 있는 점 (선분 위는 삼각형 내부가 아니기 때문에, 선 위에 있는 점은 없음)
        inside_dots = []

        triangle_dots = list(set(chain(*[triangle[0], triangle[1], triangle[2]])))

        for point in self.whole_points:

            if point in triangle_dots:
                continue

            if bool(Polygon(triangle_dots).intersection(Point(point))): 
                # 만들어진 삼각형 내부에 dot 이 있다면 (line 위에 있는 것도 True이기 때문에 line 위에 있는 점은 빼줘야 함)
               
                for line in triangle:
                    if bool(LineString(self.organize_points(line)).intersection(Point(point))):
                        return False, []
                else:
                    inside_dots.append(point)

        if len(inside_dots) == 0:
            return False, inside_dots, []
        
        elif len(inside_dots) > 1:
            return False, inside_dots, []
        
        else:
            inside_lines = []
            for vertex in triangle_dots:
                temp_line = self.organize_points([vertex, inside_dots[0]])
                if temp_line in self.drawn_lines_copy:
                    inside_lines.append(temp_line)


            return True, inside_dots, inside_lines

    # Score Checking Functions
    def return_fooling_triangles(self) -> dict:
        """
        현재 map에 낚시 삼각형 후보, 낚시 삼각형, 낚시 당한 삼각형을 모두 반환하는 함수입니다.

        input : -

        output : {
            "candidate_fooling_triangles" : [], # 중심에서 꼭짓점으로 선을 그음으로써 낚시 삼각형으로 만들 수 있는 후보 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
            "fooling_triangles" : [], # 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
            "fooled_triangles" : [] # 상대방이 낚시 당한 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
                  }
        """
        # Line: [(x1, y1), (x2, y2)]
        # triangle: [Line, Line, Line]
        # triangles: [triangle, triangle, ...]

        result = {
            "candidate_fooling_triangles" : [], # 중심에서 꼭짓점으로 선을 그음으로써 낚시 삼각형으로 만들 수 있는 후보 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
            "fooling_triangles" : [], # 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
            "fooled_triangles" : [] # 상대방이 낚시 당한 낚시 삼각형들의 dots, lines -> List[List[List[Point, ...], List[Line, ...]], ...]
                  }

        triangles = self.return_triangles()

        for triangle in triangles:

            is_fooling_triangle, inside_dots, inside_lines = self.is_fooling_triangle(triangle)

            if is_fooling_triangle:

                if len(inside_lines) == 0:
                    # 삼각형 내부에 점이 있지만, 0개의 선이 그어져 있으면 -> 상대방에게 낚시를 할 수 있는 상황인지 확인하는 용도
                    candidate_fooling_triangle_dots = [*self.return_dots_from_lines(triangle), *inside_dots]
                    candidate_fooling_triangle_lines = list(map(self.organize_points, [*triangle, *inside_lines]))
                    candidate_fooling_triangle = [candidate_fooling_triangle_dots, candidate_fooling_triangle_lines]
                    result["candidate_fooling_triangles"].append(candidate_fooling_triangle)

                elif len(inside_lines) == 1:
                    # 삼각형 내부에 점이 있고, 1개의 선이 그어져 있으면 -> 절대 건들면 안되는 낚시 삼각형
                    fooling_triangle_dots = [*self.return_dots_from_lines(triangle), *inside_dots]
                    fooling_triangle_lines =list(map(self.organize_points, [*triangle, *inside_lines]))
                    fooling_triangle = [fooling_triangle_dots, fooling_triangle_lines]
                    result["fooling_triangles"].append(fooling_triangle)

                elif len(inside_lines) == 2:
                    # 삼각형 내부에 점이 있지만, 2개의 선이 그어져 있으면 -> 상대방이 낚시에 걸렸는지 확인하는 용도
                    fooled_triangle_dots = [*self.return_dots_from_lines(triangle), *inside_dots]
                    fooled_triangle_lines = list(map(self.organize_points, [*triangle, *inside_lines]))
                    fooled_triangle = [fooled_triangle_dots, fooled_triangle_lines]
                    result["fooled_triangles"].append(fooled_triangle)

        return result
    
    def get_candidate_fooling_triangles(self, fooling_triangles):
        candidate_fooling_triangles = fooling_triangles["candidate_fooling_triangles"]

        if candidate_fooling_triangles:

            dots = set(candidate_fooling_triangles[0][0])
            lines_dots = set(self.return_dots_from_lines(candidate_fooling_triangles[0][1]))

            # Tuple
            middle_dot = list(dots - lines_dots)[0]
            vertex = random.choice(list(lines_dots))

            return self.organize_points([middle_dot, vertex])
    
    
    def is_opponent_fooled(self, fooling_triangles):
        """
        상대방이 낚시에 당했는지 확인하는 함수입니다.

        input : -

        output : is_opponent_fooled
            is_opponent_fooled: True, False
        """
        if self.drawn_lines_copy:
            recent_line = self.drawn_lines_copy[-1]
            result = fooling_triangles

            fooled_triangles = result["fooled_triangles"]
            fooling_triangles = result["fooling_triangles"]

            if not fooled_triangles and not fooling_triangles:
                return True
            
            else:
                for fooled_triangle in fooled_triangles:
                    if recent_line in fooled_triangle[1]:
                        return True
                else:
                    return False
        
        else:
            return True
        
####################################################### 김수환 #######################################################












####################################################### 한승현 #######################################################
    # node_lines = [] // 기용 가능한 연결 후보 points이 담긴 노드 리스트
    # 사용 예시 :  minmax(depth??, -math.inf, math.inf, 미정??)
    # depth의 홀짝이나 고정값이나 max의 layer 수로 최초 maximizing_player의 True/False를 지정해준다
    # 기용 가능한 연결 후보 points가 맨 밑 노드가 되는 minmax tree
    def minmax(self, depth, alpha, beta, maximizing_player):
        # if depth == 0 or self.check_endgame():  # 기저 조건 : 깊이가 0이거나 게임 종료 상태일 때
        if depth == 0:  # 윗줄처럼 하려 했지만 종료 상태 아님이 확실하기 때문에 depth만 확인해줘도 될 것 같다
            return self.evaluate(maximizing_player)  # 현재 상태 반환
        
        """
        calculate_heuristics() 을 둬도 괜찮. 
        """

        if maximizing_player:  # max layer인지 체크
            max_eval = float('-inf')
            for child in self.possible_moves():  # 가능한 노드들 탐색 함수. 이미 결과값 있다면 해당 points 리스트로 변경 가능
                eval = child.minmax(depth - 1, alpha, beta, False)  # depth+1로 진행시켜도 됨, 최대 depth 값을 제한한다면.
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:  # cutoff
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for child in self.possible_moves():
                eval = child.minmax(depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval



    def evaluate(self, maximizing_player):
        # 해당 라인을 그어 점수를 얼마나 획득할 수 있는지 평가.
        count = count_now_avail_tri()  #현재 상태에서 만들 수 있는 삼각형이 몇개인지 계산하는 함수. 기존 가용 삼각형 개수 세는 함수에 count 변수만 추가해도 된다.
        if maximizing_player:
            machine_score = machine_score + count  #machine_score는 실제 스코어에 임시 추가 점수를 더한 값이다. machine_score를 구하는 코드 구현해야 함.
            return machine_score
        else:
            user_score = user_score + count  #user_score는 실제 스코어에 임시 추가 점수를 더한 값이다. user_score를 구하는 코드 구현해야 함.
            return user_score
        
        # 단순히 스코어로만 계산할게 아닌, 당장 얻을 수 있는 점수가 큰지 판단해서(그런 점에겐 더 큰 점수 부여) 리턴해도 됨

    def possible_moves(self):
        # 가능한 가능한 노드들 탐색 함수
        return []
    
    
    def get_available_lines(self):
        return [[point1, point2] for (point1, point2) in list(combinations(self.whole_points, 2)) if self.check_availability([point1, point2])]
    
####################################################### 한승현 #######################################################
                    
    
