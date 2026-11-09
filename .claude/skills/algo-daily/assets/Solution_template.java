/*
 * 문제  : {{TITLE}} ({{PLATFORM}} {{ID}}, Lv.{{LEVEL}})
 * 링크  : {{URL}}
 * 유형  : {{TYPE_NAME}}
 * 목표  : {{TARGET}}분   시작: {{START_TIME}}
 *
 * 실행: java {{FILENAME}}
 * 성공 기준: 콘솔에 "ALL PASS"가 찍힐 때까지가 1차 완료다.
 *            제출 전 반드시 edge1/edge2에 스스로 만든 반례를 채운다 —
 *            제공된 예제만 통과하고 제출해서 틀리는 게 가장 흔한 실점이다.
 */
import java.util.*;

public class {{CLASS}} {

    // ---- 풀이 ----
    static {{RETURN_TYPE}} solution({{PARAMS}}) {
        return {{DEFAULT_RETURN}};
    }

    // ---- 검증 ----
    public static void main(String[] args) {
        int fail = 0;

        // 문제에 주어진 예제
        fail += check("예제1", {{EXPECTED_1}}, solution({{ARGS_1}})) ? 0 : 1;

        // 스스로 만든 반례 — 빈 입력 / 원소 1개 / 최댓값 / 동일값 / 경계
        // fail += check("edge1 빈입력", ?, solution(?)) ? 0 : 1;
        // fail += check("edge2 최댓값", ?, solution(?)) ? 0 : 1;

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
