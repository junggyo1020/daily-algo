package daily.d{{YYYYMMDD}};

/*
 * 문제  : {{TITLE}} ({{PLATFORM}} {{ID}}, Lv.{{LEVEL}})
 * 링크  : {{URL}}
 * 유형  : {{TYPE_NAME}}
 * 목표  : {{TARGET}}분   시작: {{START_TIME}}
 *
 * 실행: java {{FILEPATH}}
 * 성공 기준: 콘솔에 "ALL PASS"가 찍힐 때까지가 1차 완료다.
 *            예제 아래의 반례까지 통과해야 한다.
 *            제공된 예제만 통과하고 제출해서 틀리는 게 가장 흔한 실점이다.
 *
 * 제출: 아래 "붙여넣기 시작" 줄부터 파일 끝까지 복사해 프로그래머스 에디터에 넣는다.
 *       채점기는 class Solution 과 인스턴스 메서드 solution 을 찾는다.
 */
import java.util.*;

public class {{CLASS}} {

    public static void main(String[] args) {
        Solution s = new Solution();
        int fail = 0;

        // 문제에 주어진 예제
        fail += check("예제1", {{EXPECTED_1}}, s.solution({{ARGS_1}})) ? 0 : 1;

        // 반례 (왜 이 입력을 고의로 넣는지 한 줄씩 적는다)
        fail += check("edge1 {{EDGE_1_NAME}}", {{EDGE_1_EXPECTED}}, s.solution({{EDGE_1_ARGS}})) ? 0 : 1;
        fail += check("edge2 {{EDGE_2_NAME}}", {{EDGE_2_EXPECTED}}, s.solution({{EDGE_2_ARGS}})) ? 0 : 1;

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

    public {{RETURN_TYPE}} solution({{PARAMS}}) {
        return {{DEFAULT_RETURN}};
    }
}
