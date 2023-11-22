import random
from itertools import combinations
from shapely.geometry import LineString, Point

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
        self.board_size = 7 # 7 x 7 Matrix
        self.num_dots = 0
        self.whole_points = []
        self.location = []
        self.triangles = [] # [(a, b), (c, d), (e, f)]

    def find_best_selection(self):
        available = [[point1, point2] for (point1, point2) in list(combinations(self.whole_points, 2)) if self.check_availability([point1, point2])]
        return random.choice(available)

    #5.외부와 연결되지 않은 두 선분 찾는 함수
    def find_unconnected_lines(self):
        for line1 in self.drawn_lines:
            for line2 in self.drawn_lines:
                if line1 != line2 and not self.is_line_connected(line1, line2): #and not self.has_point_inside(line1, line2):
                    return line1, line2
        return None

    def is_line_connected(self, line1, line2):
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
    
    def has_point_inside(self, line1, line2):
        # Extract coordinates of the four points
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Check if any whole_points, excluding the points of line1 and line2, are inside the polygon
        points_to_check = set(self.whole_points) - set([line1[0], line1[1], line2[0], line2[1]])
        inside_polygon = any(polygon.contains(Point(point)) for point in points_to_check)

        # If any whole_points are inside, return True; otherwise, return False
        return not inside_polygon


    #6.외부와 연결되지 않은 두 선분으로 만들 수 있는 선분의 개수 구하는 함수
    def count_possible_lines(self, line1, line2):
        count = 0
        for point1 in line1:
            for point2 in line2:
                if point1 != point2 and self.check_availability([point1, point2]):
                    count += 1
        return count

    def is_diagonal_blocked(self, line1, line2):
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        # Check if the lines are diagonals and if they block each other
        if (x1 - x2) * (y3 - y4) == (y1 - y2) * (x3 - x4):
            # Check if the lines cross each other
            line1 = LineString([line1[0], line1[1]])
            line2 = LineString([line2[0], line2[1]])
            return line1.crosses(line2)
        else:
            return False
    
    
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
        for l in self.drawn_lines:
            if len(list(set([line[0], line[1], l[0], l[1]]))) == 3:
                continue
            elif bool(line_string.intersection(LineString(l))):
                condition3 = False

        # Must be a new line
        condition4 = (line not in self.drawn_lines)

        if condition1 and condition2 and condition3 and condition4:
            return True
        else:
            return False    

    
    def check_get2point(self):
            candidate = []
            count = 0
            for (point1, point2) in list(combinations(self.whole_points, 2)):
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
        for previousLine in self.drawn_lines:

            # 한 선분의 양 끝 점에 연결된 다른 선분들 찾기
            point1 = previousLine[0]
            point2 = previousLine[1]
            point1_connected = [] 
            point2_connected = []
            for l in self.drawn_lines:
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
        
        if candidate:
            return candidate[0]



    def countNoScoreActions(self):
        candidate = []
        count = 0
        for (point1, point2) in list(combinations(self.whole_points, 2)):
            if self.check_availability([point1, point2]): # 이 선이 그릴 수 있는 선인지?
                newLine = self.organize_points([point1, point2])
                self.drawn_lines.append(newLine) # 그릴 수 있는 선이라면 그렸다고 가정하고 리스트에 추가
                if self.check_get1point() == None: # 그린 상황에서 점수가 발생하는지 확인
                    candidate.append(newLine)
                    count += 1
                    print(point1, point2)
                self.drawn_lines.remove(newLine) # 넣었던 선 다시 삭제
        print("NoScoreAction : " + str(count))
        if candidate:
            return random.choice(candidate)


    def check_triangleCount(self, line):
        get_score_count = 0

        point1 = line[0]
        point2 = line[1]

        point1_connected = [] # 방금 그은 선의 두 점에 이미 그어진 line을 담는 배열
        point2_connected = []

        for l in self.drawn_lines:
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



    def is_triangle(self, dots):
        # Line: [(x1, y1), (x2, y2)]
        # lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]]

        if len(dots) == 3: # if is triangle
            return True
        else:
            return False
        
    def return_dots_from_lines(self, lines):
        return self.organize_points(list(set(chain(*[*lines]))))
        
    def is_occupied(self, dots):
        # Line: [(x1, y1), (x2, y2)]
        # lines: [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)], [(x1, y1), (x2, y2)]]
        triangle = self.organize_points(list(dots))

        if triangle in self.triangles: # if is triangle
            return True
        else:
            return False

    # return if line makes triangles (includes no-score triangle)
    def return_triangles(self):
        triangles = []
        line_combinations = combinations(self.drawn_lines, 3)

        # for all 3-line combinations (nC3)
        for line_combination in line_combinations:

            # all dots from all lines
            dots = set(chain(*[line_combination[0], line_combination[1], line_combination[2]]))
            
            # if 3-line combination is triangle and not occupied
            if self.is_triangle(dots) and not self.is_occupied(dots):
                triangles.append(line_combination)

        return triangles
    

    def is_fooling_triangle(self, triangle):
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
                if temp_line in self.drawn_lines:
                    inside_lines.append(temp_line)


            return True, inside_dots, inside_lines


    # Score Checking Functions
    def return_fooling_triangles(self):
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
    
    def is_opponent_fooled(self):
        if self.drawn_lines:
            recent_line = self.drawn_lines[-1]
            result = self.return_fooling_triangles()

            fooled_triangles = result["fooled_triangles"]

            for fooled_triangle in fooled_triangles:
                if recent_line in fooled_triangle[1]:
                    return True
            else:
                return False
        
        else:
            return False

        
                

                    
    def organize_points(self, point_list):
        point_list.sort(key=lambda x: (x[0], x[1]))
        return point_list