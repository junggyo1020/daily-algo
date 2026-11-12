package daily.d20261112;

/*
 * 문제  : 문자열 압축 (프로그래머스 60057, Lv.2, 2020 KAKAO BLIND)
 * 링크  : https://school.programmers.co.kr/learn/courses/30/lessons/60057
 * 유형  : 문자열
 * 목표  : 25분   시작: 23:17
 *
 * 실행: java src/main/java/daily/d20261112/D20261112_60057_StringCompression.java
 * 성공 기준: 콘솔에 "ALL PASS"
 *
 * 제출: 아래 "붙여넣기 시작" 줄부터 파일 끝까지 복사해 프로그래머스 에디터에 넣는다.
 *
 * 제출 전 edge1, edge2에 스스로 만든 반례를 채운다.
 * 반례는 문제의 제한사항 안에서 만든다.
 */
import java.util.*;

public class D20261112_60057_StringCompression {

    public static void main(String[] args) {
        Solution s = new Solution();
        int fail = 0;

        fail += check("예제1", 7,  s.solution("aabbaccc")) ? 0 : 1;
        fail += check("예제2", 9,  s.solution("ababcdcdababcdcd")) ? 0 : 1;
        fail += check("예제3", 8,  s.solution("abcabcdede")) ? 0 : 1;
        fail += check("예제4", 14, s.solution("abcabcabcabcdededededede")) ? 0 : 1;
        fail += check("예제5", 17, s.solution("xababcdcdababcdcd")) ? 0 : 1;

        // 스스로 만든 반례 — 길이 1, 전부 같은 문자, 압축이 전혀 안 되는 경우 등
        // fail += check("edge1 ...", ?, s.solution("?")) ? 0 : 1;
        // fail += check("edge2 ...", ?, s.solution("?")) ? 0 : 1;

        System.out.println(fail == 0 ? "ALL PASS" : fail + " FAIL");
    }

    static boolean check(String name, Object expected, Object actual) {
        String e = String.valueOf(expected), a = String.valueOf(actual);
        boolean ok = e.equals(a);
        System.out.printf("%-16s %s  expected=%s actual=%s%n", name, ok ? "PASS" : "FAIL", e, a);
        return ok;
    }
}

// ===================== 붙여넣기 시작 (import 줄도 함께 복사) =====================
class Solution {

	static StringBuilder sb;
	static StringBuilder result;
	static String answer;
	static int minLen;

    public int solution(String s) {
		char[] ch = s.toCharArray();

        //문자열 자르는 단위 순회
		minLen = s.length();
		for(int k = 1; k <= s.length(); k++) {
			String prev = "";
			result = new StringBuilder();
			int cnt = 1;

			int lastIdx = 0;
			for(int i = 0; i+k < s.length(); i+=k) {
				sb = new StringBuilder();
				for(int j = i; j < i+k; j++) {
					sb.append(ch[j]);
				}
				if(prev.equals(sb.toString())) {
					cnt++;
				} else {
					if(cnt > 1) result.append(cnt);
					result.append(sb);
					prev = sb.toString();
					cnt = 1;
				}
				lastIdx = i+k;
			}

			//나머지 부분 채우기
			sb = new StringBuilder();
			for(int i = lastIdx; i < s.length(); i++) {
				sb.append(ch[i]);
			}

			if(prev.equals(sb.toString())) {
				cnt++;
			} else {
				if(cnt > 1) result.append(cnt);
				result.append(sb);
				prev = sb.toString();
				cnt = 1;
			}

			if(result.length() < minLen) minLen = result.length();
		}

		return minLen;
    }
}
