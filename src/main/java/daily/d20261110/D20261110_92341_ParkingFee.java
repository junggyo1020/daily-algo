package daily.d20261110;

/*
 * 문제  : 주차 요금 계산 (프로그래머스 92341, Lv.2, 2022 KAKAO BLIND)
 * 링크  : https://school.programmers.co.kr/learn/courses/30/lessons/92341
 * 유형  : 구현과 시뮬레이션
 * 목표  : 25분   실제: 76분 (1차 35분, 2차 41분)
 * 결과  : 힌트 후 정답, 프로그래머스 정확성 100.0
 *
 * 실행: java src/main/java/daily/d20261110/D20261110_92341_ParkingFee.java
 * 제출: 아래 "붙여넣기 시작" 줄부터 파일 끝까지 복사해 프로그래머스 에디터에 넣는다.
 */
import java.util.*;

public class D20261110_92341_ParkingFee {

    public static void main(String[] args) {
        Solution s = new Solution();
        int fail = 0;

        fail += check("예제1",
                new int[]{14600, 34400, 5000},
                s.solution(new int[]{180, 5000, 10, 600}, new String[]{
                        "05:34 5961 IN", "06:00 0000 IN", "06:34 0000 OUT", "07:59 5961 OUT",
                        "07:59 0148 IN", "18:59 0000 IN", "19:09 0148 OUT", "22:59 5961 IN",
                        "23:00 5961 OUT"})) ? 0 : 1;

        fail += check("예제2",
                new int[]{0, 591},
                s.solution(new int[]{120, 0, 60, 591}, new String[]{
                        "16:00 3961 IN", "16:00 0202 IN", "18:00 3961 OUT",
                        "18:00 0202 OUT", "23:58 3961 IN"})) ? 0 : 1;

        fail += check("예제3",
                new int[]{14841},
                s.solution(new int[]{1, 461, 1, 10}, new String[]{"00:00 1234 IN"})) ? 0 : 1;

        // 직접 만든 반례
        fail += check("edge1 미출차 2대",
                new int[]{80600, 80600},
                s.solution(new int[]{180, 5000, 10, 600},
                        new String[]{"00:00 1111 IN", "00:00 2222 IN"})) ? 0 : 1;

        fail += check("edge2 기본시간 경계",
                new int[]{5000},
                s.solution(new int[]{180, 5000, 10, 600},
                        new String[]{"00:00 1111 IN", "03:00 1111 OUT"})) ? 0 : 1;

        System.out.println(fail == 0 ? "ALL PASS" : fail + " FAIL");
    }

    static boolean check(String name, Object expected, Object actual) {
        String e = stringify(expected), a = stringify(actual);
        boolean ok = e.equals(a);
        System.out.printf("%-16s %s  expected=%s actual=%s%n", name, ok ? "PASS" : "FAIL", e, a);
        return ok;
    }

    static String stringify(Object o) {
        if (o instanceof int[] x)    return Arrays.toString(x);
        if (o instanceof long[] x)   return Arrays.toString(x);
        if (o instanceof String[] x) return Arrays.toString(x);
        if (o instanceof int[][] x)  return Arrays.deepToString(x);
        return String.valueOf(o);
    }
}

// ===================== 붙여넣기 시작 (import 줄도 함께 복사) =====================
class Solution {

    public int[] solution(int[] fees, String[] records) {
        HashMap<String, String> parkingSpace = new HashMap<>(); //주차장(차량번호, 시각)
        TreeMap<String, Integer> timeForCar = new TreeMap<>(); //차량별 주차시간

        for (int i = 0; i < records.length; i++) {
            StringTokenizer st = new StringTokenizer(records[i]);

            String time = st.nextToken();
            String carNum = st.nextToken();
            String op = st.nextToken();

            //입차
            if (op.equals("IN")) {
                parkingSpace.put(carNum, time);
            }
            //출차
            else {
                String in = parkingSpace.get(carNum);
                int diff = calDiff(time, in);
                timeForCar.put(carNum, timeForCar.getOrDefault(carNum, 0) + diff);
                parkingSpace.remove(carNum);
            }
        }

        //주차장에 남아있는 차량은 23:59 로 마감
        for (Map.Entry<String, String> car : parkingSpace.entrySet()) {
            String inNum = car.getKey();
            String inTime = car.getValue();
            int diff2 = calDiff("23:59", inTime);
            timeForCar.put(inNum, timeForCar.getOrDefault(inNum, 0) + diff2);
        }

        //요금 정산
        int[] answer = new int[timeForCar.size()];
        int cnt = 0;
        for (Integer x : timeForCar.values()) {
            int sum = 0;

            if (x <= fees[0]) sum += fees[1];
            else {
                int num = x - fees[0];
                sum += (fees[1] + (num + fees[2] - 1) / fees[2] * fees[3]); //올림 공식
            }

            answer[cnt++] = sum;
        }

        return answer;
    }

    private int calDiff(String out, String in) {
        int hOut = Integer.parseInt(out.substring(0, 2));
        int hIn = Integer.parseInt(in.substring(0, 2));
        int mOut = Integer.parseInt(out.substring(3));
        int mIn = Integer.parseInt(in.substring(3));

        return (hOut - hIn) * 60 + (mOut - mIn);
    }
}
