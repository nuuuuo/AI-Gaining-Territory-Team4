import random
from itertools import combinations, chain, product
from shapely.geometry import LineString, Point, Polygon
import copy
import math

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
        self.minmax_mode = False
        self.search_depth = 3

    def find_best_selection(self):
        start = time.time()
        line = None
        self.drawn_lines_copy = copy.deepcopy(self.drawn_lines)

        fooling_triangles = self.return_fooling_triangles()

        if self.is_opponent_fooled(fooling_triangles) and self.is_opponent_fooled_flag:
            self.is_opponent_fooled_flag = True
        else:
            self.is_opponent_fooled_flag = False

        print("FIND START")

        if self.score[1] > 0 and self.score[1] <= self.score[0]: # machine이 지기 시작하면
            self.minmax_mode = True

        
        if (lines := self.check_get2point()) != None: # lines = None or [line, line ...]
            if self.minmax_mode:
                line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            else:
                line = lines[0]
            print("choice : "+str(line))
            # return line
        # 1점 얻을 수 있는 액션 있는지 확인, 있으면 낚시 상황 있는지 확인
        elif (lines := self.check_get1point()) != None:
            if self.minmax_mode:
                line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            else:
                line = lines[0]
            print("choice : "+str(line))
            # return line
        # 상대방이 낚시에 당하면 낚시 시도
        elif self.is_opponent_fooled_flag and (lines := self.get_candidate_fooling_triangles(fooling_triangles)) != None:
            if self.minmax_mode:
                line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            else:
                line = lines[0]
            print("choice : "+str(line))
            # return line
        elif (lines := self.countNoScoreActions()) != None:
            if self.minmax_mode:
                line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            else:
                result = 10000
                for l in lines:
                    self.drawn_lines_copy.append(l) # 이 선택을 했을 때에 상대방 입장에서 nocountAction을 계산하기 위해
                    count = self.countNoScoreActions_returnCount()
                    if count == 0:
                        line = l
                        self.drawn_lines_copy.remove(l)
                        break
                    elif count > 2:
                        if result > count:
                            result = count
                            line = l
                    self.drawn_lines_copy.remove(l)
                # 모든 경우에 대해서 전부 2 이하로 남는다면? minmax실시하는게 맞지 않을까
                # if line == None:
                

            if line != None:
                self.drawn_lines_copy.append(line)
                print("HOW MANY NO SCORE ACTIONS AFTER CHOICE")
                temp = self.countNoScoreActions()
                if temp == None: # 이번이 마지막 no score action 이었으면 minmax 돌리기
                    self.minmax_mode = True
                    print("minmax mode")
                print("END")
                print("choice : "+str(line))
                self.drawn_lines_copy.remove(line)
            
        elif (lines := self.find_unconnected_lines()) != None: # 핑퐁
            if self.minmax_mode:
                line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            else:
                line = lines[0]
            print("choice : "+str(line))

        else:
            lines = self.get_available_lines(self.drawn_lines_copy)[:15]
            line = self.minmax(self.search_depth, self.search_depth, float("-inf"), float("inf"), float('-inf'), float('inf'), self.drawn_lines_copy, self.score[:], True, lines)
            self.minmax_mode = True
            print("minmax mode")

        
        print("elapsed time :", time.time() - start)
            
        return line
        
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
                    # print("get2point : " + str(newLine))
        if candidate:
            return candidate
        else:
            return None

        
            
        
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
                                # print("get1point : "+ str(thirdLine))
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
                        # print("fooling line : "+ str(line))
                        break
                else:
                    candidate_final.append(line)

            if candidate_final:
                return candidate_final
            else:
                return None



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
            return candidate
        else:
            return None
        
    def countNoScoreActions_returnCount(self):
        count = 0
        for (point1, point2) in list(combinations(self.whole_points, 2)):
            if self.check_availability([point1, point2]): # 이 선이 그릴 수 있는 선인지?
                newLine = self.organize_points([point1, point2])
                self.drawn_lines_copy.append(newLine) # 그릴 수 있는 선이라면 그렸다고 가정하고 리스트에 추가
                if self.check_get1point() == None and self.check_get2point() == None: # 그린 상황에서 점수가 발생하는지 확인
                    count += 1
                    print(point1, point2)
                self.drawn_lines_copy.remove(newLine) # 넣었던 선 다시 삭제
        return count


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
    #핑퐁 선분 찾는 함수
    def find_unconnected_lines(self):
        """
        input: 

        output: 두 연결되지 않은 선분 line1 line2, 연결되지 않은 선분이 없으면 None
        """
        unconnected_lines = []
        ping_pong_lines = []
        lines_combination = list(combinations(self.drawn_lines_copy, 2))

        for line1, line2 in lines_combination:
                if line1 != line2 and not self.is_line_connected(line1, line2) and not self.has_point_inside(line1, line2) and self.count_possible_lines(line1, line2) == 3:
                    unconnected_lines.append([line1, line2])
        
        for unconnected_line_set in unconnected_lines:
            line1, line2 = unconnected_line_set

            x1, y1 = line1[0]
            x2, y2 = line1[1]
            x3, y3 = line2[0]
            x4, y4 = line2[1]

            
            for line in [[(x2, y2), (x3, y3)], [(x4, y4), (x1, y1)], [(x1, y1), (x3, y3)], [(x2, y2), (x4, y4)]]:
                if self.organize_points(line) != self.organize_points(line1) and self.organize_points(line) != self.organize_points(line2):
                    ping_pong_lines.append(line)


            return ping_pong_lines
        
        else:
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

    def polar_angle(self, point, center):
        x, y = point
        cx, cy = center
        return math.atan2(y - cy, x - cx)
    
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

        # 중심점 계산
        center_x = (x1 + x2 + x3 + x4) / 4
        center_y = (y1 + y2 + y3 + y4) / 4

        # 각 점에 대한 극좌표를 계산하고 각도를 기준으로 정렬
        sorted_points = sorted([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], key=lambda p: self.polar_angle(p, (center_x, center_y)))

        # 정렬된 점들을 다시 x1, y1, x2, y2, x3, y3, x4, y4에 할당
        x1, y1 = sorted_points[0]
        x2, y2 = sorted_points[1]
        x3, y3 = sorted_points[2]
        x4, y4 = sorted_points[3]
        
        polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Check if any whole_points, excluding the points of line1 and line2, are inside the polygon
        points_to_check = set(self.whole_points) - set([line1[0], line1[1], line2[0], line2[1]])
        inside_polygon = any(polygon.contains(Point(point)) or
                             Point(point).within(LineString([(x1, y1), (x2, y2)])) or
                             Point(point).within(LineString([(x1, y1), (x3, y3)])) or
                             Point(point).within(LineString([(x1, y1), (x4, y4)])) or
                             Point(point).within(LineString([(x2, y2), (x3, y3)])) or
                             Point(point).within(LineString([(x2, y2), (x4, y4)])) or
                             Point(point).within(LineString([(x3, y3), (x4, y4)])) for point in points_to_check)

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

            return [self.organize_points([middle_dot, vertex])]
        
        else: 
            return None
    
    
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
    # score = [machine(우리팀), user(상대팀)]
    def minmax(self, init_depth, depth, parent_alpha, parent_beta, alpha, beta, cur_map, score, maximizing_player, search_line_list):
        # if depth == 0 or self.check_endgame():  # 기저 조건 : 깊이가 0이거나 게임 종료 상태일 때
        # with open("min_max_log.txt", "a") as f:
            # f.write(str(cur_map) + "\n")

        if depth == 0 or len(self.get_available_lines(cur_map)) == 0:  # 윗줄처럼 하려 했지만 종료 상태 아님이 확실하기 때문에 depth만 확인해줘도 될 것 같다
            eval = score[1] - score[0]
            # print(score)
            # print("leaf node")
            # print("eval: ", eval)
            return alpha, beta, eval, True  # 현재 상태 반환 == 휴리스틱 반환
                
        """
        calculate_heuristics() 을 둬도 괜찮. 
        """

        if init_depth == depth:
            lines = search_line_list
        else:
            lines = self.get_available_lines(cur_map)

        if maximizing_player:  # max layer인지 체크
            alpha = float('-inf')
            max_line = None
            for line in lines:  # 가능한 노드들 탐색 함수. 이미 결과값 있다면 해당 points 리스트로 변경 가능
                cur_map_copy = copy.deepcopy(cur_map)
                cur_map_copy.append(line)
                next_map = cur_map_copy
                changed_score = [score[0], score[1] + self.check_triangleCount_map(line, next_map)]

                child_alpha, child_beta, eval, child_is_leaf = self.minmax(init_depth, depth - 1, alpha, beta, float("-inf"), float("inf"), next_map, changed_score, False, [])  # depth+1로 진행시켜도 됨, 최대 depth 값을 제한한다면.

                if child_is_leaf:
                    if eval > alpha:
                        alpha = eval
                        max_line = line
                else:
                    if child_beta > alpha:
                        alpha = child_beta
                        max_line = line

                if alpha >= parent_beta:  # cutoff
                    # print("cutoff in max")
                    # print("alpha:", alpha)
                    # print("parent_beta:", parent_beta)
                    # parent_beta : 형제 노드의 평가값 중 가장 작은 값
                    # alpha : 자식 노드의 평가값 중 가장 큰 값
                    # 내가 max를 뽑으므로, 내 alpha가 parent_beta보다 커지면, 더이상 보는 의미가 없음
                    break
            
            if init_depth == depth: # root일 때
                return max_line
            else:
                return alpha, beta, 0, False 
        
        else: # min layer
            beta = float('inf')
            min_line = None
            for line in lines:  # 가능한 노드들 탐색 함수. 이미 결과값 있다면 해당 points 리스트로 변경 가능
                cur_map_copy = copy.deepcopy(cur_map)
                cur_map_copy.append(line)
                next_map = cur_map_copy
                changed_score = [score[0] + self.check_triangleCount_map(line, next_map), score[1]]
                child_alpha, child_beta, eval, child_is_leaf = self.minmax(init_depth, depth - 1, alpha, beta, float("-inf"), float("inf"), next_map, changed_score, True, [])  # depth+1로 진행시켜도 됨, 최대 depth 값을 제한한다면.

                if child_is_leaf:
                    if eval < beta:
                        beta = eval
                        min_line = line
                else:
                    if child_alpha < beta:
                        beta = child_alpha
                        min_line = line

                if beta <= parent_alpha:  # cutoff
                    # print("cutoff in min")
                    # print("beta:", beta)
                    # print("parent_alpha:", parent_alpha)
                    # parent_alpha : 형제 노드의 평가값 중 가장 큰 값
                    # beta : 자식 노드의 평가값 중 가장 작은 값
                    # 내가 min을 뽑고 parent가 max를 뽑으므로, 내 beta가 parent_alpha보다 작아면, 더이상 보는 의미가 없음
                    break
                
            return alpha, beta, 0, False 

    def evaluate(self, map, is_maximizing):
        # 상황 평가하는 함수 == 그 상황에 대한 휴리스틱 구하는 함수
        # 해당 라인을 그어 점수를 얼마나 획득할 수 있는지 평가.

        # get 1 score +
        # get 2 score + 
        # 마주보는 선분 개수 +
        # 상대방이 낚시에 당할 때 낚시 삼각형을 만들 수 있으면 +
        # 

        possible_lines = self.possible_moves(map)
        max_triangles = 0
        sum_triangles = 0

        for line in possible_lines:
            available_triangles = self.check_triangleCount_map(line, map)
            max_triangles = max(available_triangles, max_triangles)
            sum_triangles += available_triangles

        # return max_triangles
        return sum_triangles


        count = count_now_avail_tri()  #현재 상태에서 만들 수 있는 삼각형이 몇개인지 계산하는 함수. 기존 가용 삼각형 개수 세는 함수에 count 변수만 추가해도 된다.
        if maximizing_player:
            machine_score = machine_score + count  #machine_score는 실제 스코어에 임시 추가 점수를 더한 값이다. machine_score를 구하는 코드 구현해야 함.
            return machine_score
        else:
            user_score = user_score + count  #user_score는 실제 스코어에 임시 추가 점수를 더한 값이다. user_score를 구하는 코드 구현해야 함.
            return user_score
        
        # 단순히 스코어로만 계산할게 아닌, 당장 얻을 수 있는 점수가 큰지 판단해서(그런 점에겐 더 큰 점수 부여) 리턴해도 됨

    def possible_moves(self, map):
        # 가능한 가능한 노드들 탐색 함수
        # 현재 그을 수 있는 선분 반환 하는 함수
        lines = []

        lines.append(self.check_get2point())
        lines.append(self.check_get1point())

        return self.get_available_lines(map)
    
    
    def get_available_lines(self, map):
        return [[point1, point2] for (point1, point2) in list(combinations(self.whole_points, 2)) if self.check_availability_map([point1, point2], map)]
    
    def check_availability_map(self, line, map):
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
        for l in map:
            if len(list(set([line[0], line[1], l[0], l[1]]))) == 3:
                continue
            elif bool(line_string.intersection(LineString(l))):
                condition3 = False

        # Must be a new line
        condition4 = (line not in map)

        if condition1 and condition2 and condition3 and condition4:
            return True
        else:
            return False   
        
    def check_triangleCount_map(self, line, map):
        get_score_count = 0

        point1 = line[0]
        point2 = line[1]

        point1_connected = [] # 방금 그은 선의 두 점에 이미 그어진 line을 담는 배열
        point2_connected = []

        for l in map:
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

    
####################################################### 한승현 #######################################################
                    
    
