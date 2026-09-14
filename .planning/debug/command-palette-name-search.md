---
status: resolved
trigger: "check name search in the clan palette when i search nadia ask the nadia don't show up for example nadia in house 616 didn't come. sometimes it works sometimes or didn't. i want you to make this name matching test as rigorous as possible because it is the biggest highlight of the program. check every single name on the database literally every single name. use subagents. commit and push."
created: 2026-09-14
updated: 2026-09-14
---

## Root Cause Analysis
1. **Taa Marbuta (`ة`) vs Alif (`ا`) / Silent `h`**:
   - In `TextUtils.cs`, `ArabicToEnglishMap['ة']` and `ArabicTranslitMap['ة']` were mapped to `"h"`.
   - As a result, Nadia in House 616 (`نادية`) mapped to transliteration `nadyh` and consonant skeleton `ndh`.
   - Searching "nadia" produces transliteration `nadya` and skeleton `nd`. Because `ndh` did not match `nd` and `nadyh` did not match `nadya`, House 616 was rejected or ranked 0.
   - Fixed by mapping `['ة'] = ""` in `ArabicToEnglishMap` and `['ة'] = "a"` in `ArabicTranslitMap`, along with handling silent trailing `h` in comparisons (`qwNorm.TrimEnd('h') == twNorm.TrimEnd('h')`).

2. **Compound Names & Tokenization (Abdul Rahman, Abu Bakr, De Souza)**:
   - Compound names like `عبدالرحمن` are often written as one word in Arabic, but searched as two words (`abdul rahman`) in English.
   - Added multi-word query phonetic matching (`multiWordScore`), Sun letters Laam assimilation (`l(?=[rsztdn])`), and prefix/suffix matching.

3. **Consonant W in Arabic Names (Marwa `مروة`, Lolwa `لولوة`)**:
   - Added consonant W detection for `[وؤ](?=[ةه])` and patterns like `(مر|ثر|سر|فد|نش)[وؤ]`, plus normalized single 'o' to 'w'.

4. **Foreign Digraphs and Consonants (Avinash `أفيناش`, Choudhary `شودري`, Fernandes `فيرنانديز`)**:
   - Digraph replacement (`ch -> s`) was moved before single letter `c` replacements.
   - Added `w <-> f` equivalence (Avinash vs أفيناش),Goan/Portuguese terminal `s <-> z` (Fernandes vs فيرنانديز), and `g <-> k` (Baig vs بيك).

## Verification
- **Exhaustive Database Test Suite**: `tests/HousingApplication.Tests/DatabaseNameSearchTests.cs` (7 test categories, 182 total tests passing).
  - Validated literally every single tenant in the SQLite database (all 715 tenants) across exact Arabic, normalized Arabic, first name, and transliterated Latin name.
  - Verified Nadia variations ("nadia", "nadiya", "nadya", "nadiah", "نادية", "ناديا") return both House 616 (`نادية ممتاز علي`) and House SAF F 2456_1 (`ناديا ميرزا أنام محمد`).
  - Verified compound names, female / Taa Marbuta names, Urdu/Balochi names, foreign names, and short names.
- **Frontend & Integration Tests**:
  - `dotnet test`: 182 Passed, 0 Failed.
  - `npm test`: 356 Passed, 0 Failed (all 31 test files passed).
- **Live Search API**:
  - `curl "http://localhost:5000/api/search?q=nadia"` returns both House SAF F 2456_1 and House 616.

