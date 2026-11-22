-- READ-ONLY exact source-copy key/value concordance for 2017 source rows inside the frozen 263 1h-to-<24h target gaps. No inference of omission cause or restoration eligibility.
WITH gaps AS (
SELECT 1 AS gap_no, 1483214100 AS left_time, 1483288200 AS right_time UNION ALL
SELECT 2 AS gap_no, 1483294800 AS left_time, 1483299000 AS right_time UNION ALL
SELECT 3 AS gap_no, 1483514400 AS left_time, 1483523100 AS right_time UNION ALL
SELECT 4 AS gap_no, 1483793700 AS left_time, 1483797300 AS right_time UNION ALL
SELECT 5 AS gap_no, 1483913400 AS left_time, 1483938000 AS right_time UNION ALL
SELECT 6 AS gap_no, 1484676000 AS left_time, 1484688300 AS right_time UNION ALL
SELECT 7 AS gap_no, 1484721600 AS left_time, 1484758500 AS right_time UNION ALL
SELECT 8 AS gap_no, 1484897700 AS left_time, 1484902200 AS right_time UNION ALL
SELECT 9 AS gap_no, 1484902800 AS left_time, 1484907900 AS right_time UNION ALL
SELECT 10 AS gap_no, 1485576600 AS left_time, 1485580500 AS right_time UNION ALL
SELECT 11 AS gap_no, 1485744300 AS left_time, 1485748500 AS right_time UNION ALL
SELECT 12 AS gap_no, 1489930800 AS left_time, 1489935000 AS right_time UNION ALL
SELECT 13 AS gap_no, 1490142000 AS left_time, 1490146500 AS right_time UNION ALL
SELECT 14 AS gap_no, 1490157900 AS left_time, 1490164200 AS right_time UNION ALL
SELECT 15 AS gap_no, 1490256000 AS left_time, 1490260500 AS right_time UNION ALL
SELECT 16 AS gap_no, 1490261700 AS left_time, 1490265600 AS right_time UNION ALL
SELECT 17 AS gap_no, 1490295600 AS left_time, 1490299200 AS right_time UNION ALL
SELECT 18 AS gap_no, 1490318700 AS left_time, 1490322300 AS right_time UNION ALL
SELECT 19 AS gap_no, 1490323800 AS left_time, 1490328900 AS right_time UNION ALL
SELECT 20 AS gap_no, 1490763000 AS left_time, 1490771400 AS right_time UNION ALL
SELECT 21 AS gap_no, 1490773200 AS left_time, 1490783400 AS right_time UNION ALL
SELECT 22 AS gap_no, 1490797500 AS left_time, 1490801700 AS right_time UNION ALL
SELECT 23 AS gap_no, 1490811900 AS left_time, 1490816100 AS right_time UNION ALL
SELECT 24 AS gap_no, 1491307800 AS left_time, 1491314100 AS right_time UNION ALL
SELECT 25 AS gap_no, 1491737100 AS left_time, 1491741300 AS right_time UNION ALL
SELECT 26 AS gap_no, 1491770700 AS left_time, 1491775500 AS right_time UNION ALL
SELECT 27 AS gap_no, 1491777900 AS left_time, 1491787500 AS right_time UNION ALL
SELECT 28 AS gap_no, 1491792600 AS left_time, 1491796800 AS right_time UNION ALL
SELECT 29 AS gap_no, 1491829200 AS left_time, 1491835200 AS right_time UNION ALL
SELECT 30 AS gap_no, 1491854100 AS left_time, 1491865200 AS right_time UNION ALL
SELECT 31 AS gap_no, 1493016000 AS left_time, 1493040600 AS right_time UNION ALL
SELECT 32 AS gap_no, 1493294400 AS left_time, 1493305200 AS right_time UNION ALL
SELECT 33 AS gap_no, 1493348400 AS left_time, 1493352300 AS right_time UNION ALL
SELECT 34 AS gap_no, 1493458500 AS left_time, 1493463000 AS right_time UNION ALL
SELECT 35 AS gap_no, 1493729700 AS left_time, 1493733600 AS right_time UNION ALL
SELECT 36 AS gap_no, 1493736900 AS left_time, 1493742000 AS right_time UNION ALL
SELECT 37 AS gap_no, 1493742300 AS left_time, 1493748000 AS right_time UNION ALL
SELECT 38 AS gap_no, 1493748600 AS left_time, 1493754600 AS right_time UNION ALL
SELECT 39 AS gap_no, 1493790000 AS left_time, 1493794500 AS right_time UNION ALL
SELECT 40 AS gap_no, 1493795400 AS left_time, 1493809200 AS right_time UNION ALL
SELECT 41 AS gap_no, 1493811000 AS left_time, 1493819100 AS right_time UNION ALL
SELECT 42 AS gap_no, 1493819400 AS left_time, 1493823000 AS right_time UNION ALL
SELECT 43 AS gap_no, 1493895000 AS left_time, 1493898600 AS right_time UNION ALL
SELECT 44 AS gap_no, 1493912400 AS left_time, 1493916000 AS right_time UNION ALL
SELECT 45 AS gap_no, 1493916900 AS left_time, 1493926500 AS right_time UNION ALL
SELECT 46 AS gap_no, 1493937900 AS left_time, 1493987400 AS right_time UNION ALL
SELECT 47 AS gap_no, 1493997900 AS left_time, 1494002100 AS right_time UNION ALL
SELECT 48 AS gap_no, 1494090900 AS left_time, 1494095700 AS right_time UNION ALL
SELECT 49 AS gap_no, 1494102000 AS left_time, 1494107100 AS right_time UNION ALL
SELECT 50 AS gap_no, 1494125700 AS left_time, 1494142500 AS right_time UNION ALL
SELECT 51 AS gap_no, 1494143400 AS left_time, 1494153600 AS right_time UNION ALL
SELECT 52 AS gap_no, 1494168300 AS left_time, 1494171900 AS right_time UNION ALL
SELECT 53 AS gap_no, 1494178800 AS left_time, 1494188400 AS right_time UNION ALL
SELECT 54 AS gap_no, 1494267000 AS left_time, 1494270900 AS right_time UNION ALL
SELECT 55 AS gap_no, 1494271800 AS left_time, 1494275400 AS right_time UNION ALL
SELECT 56 AS gap_no, 1494275700 AS left_time, 1494281700 AS right_time UNION ALL
SELECT 57 AS gap_no, 1494282300 AS left_time, 1494286200 AS right_time UNION ALL
SELECT 58 AS gap_no, 1494288900 AS left_time, 1494293400 AS right_time UNION ALL
SELECT 59 AS gap_no, 1494301500 AS left_time, 1494351000 AS right_time UNION ALL
SELECT 60 AS gap_no, 1494435000 AS left_time, 1494439800 AS right_time UNION ALL
SELECT 61 AS gap_no, 1494440400 AS left_time, 1494444000 AS right_time UNION ALL
SELECT 62 AS gap_no, 1494510900 AS left_time, 1494514500 AS right_time UNION ALL
SELECT 63 AS gap_no, 1494514800 AS left_time, 1494521700 AS right_time UNION ALL
SELECT 64 AS gap_no, 1494522000 AS left_time, 1494531000 AS right_time UNION ALL
SELECT 65 AS gap_no, 1494531300 AS left_time, 1494537900 AS right_time UNION ALL
SELECT 66 AS gap_no, 1494538800 AS left_time, 1494553500 AS right_time UNION ALL
SELECT 67 AS gap_no, 1494553800 AS left_time, 1494564000 AS right_time UNION ALL
SELECT 68 AS gap_no, 1496039400 AS left_time, 1496043900 AS right_time UNION ALL
SELECT 69 AS gap_no, 1496056200 AS left_time, 1496061000 AS right_time UNION ALL
SELECT 70 AS gap_no, 1496193300 AS left_time, 1496199000 AS right_time UNION ALL
SELECT 71 AS gap_no, 1496202000 AS left_time, 1496209500 AS right_time UNION ALL
SELECT 72 AS gap_no, 1496217300 AS left_time, 1496222400 AS right_time UNION ALL
SELECT 73 AS gap_no, 1496470200 AS left_time, 1496479500 AS right_time UNION ALL
SELECT 74 AS gap_no, 1496502000 AS left_time, 1496512800 AS right_time UNION ALL
SELECT 75 AS gap_no, 1496515200 AS left_time, 1496526000 AS right_time UNION ALL
SELECT 76 AS gap_no, 1496526900 AS left_time, 1496531100 AS right_time UNION ALL
SELECT 77 AS gap_no, 1496533800 AS left_time, 1496542500 AS right_time UNION ALL
SELECT 78 AS gap_no, 1496550600 AS left_time, 1496554200 AS right_time UNION ALL
SELECT 79 AS gap_no, 1496561400 AS left_time, 1496567700 AS right_time UNION ALL
SELECT 80 AS gap_no, 1496571000 AS left_time, 1496594400 AS right_time UNION ALL
SELECT 81 AS gap_no, 1496653200 AS left_time, 1496658300 AS right_time UNION ALL
SELECT 82 AS gap_no, 1496658300 AS left_time, 1496687100 AS right_time UNION ALL
SELECT 83 AS gap_no, 1496759700 AS left_time, 1496770200 AS right_time UNION ALL
SELECT 84 AS gap_no, 1496788800 AS left_time, 1496793300 AS right_time UNION ALL
SELECT 85 AS gap_no, 1496794200 AS left_time, 1496798700 AS right_time UNION ALL
SELECT 86 AS gap_no, 1496833800 AS left_time, 1496840400 AS right_time UNION ALL
SELECT 87 AS gap_no, 1496841000 AS left_time, 1496844600 AS right_time UNION ALL
SELECT 88 AS gap_no, 1496845500 AS left_time, 1496849700 AS right_time UNION ALL
SELECT 89 AS gap_no, 1496856600 AS left_time, 1496861400 AS right_time UNION ALL
SELECT 90 AS gap_no, 1496863800 AS left_time, 1496870100 AS right_time UNION ALL
SELECT 91 AS gap_no, 1496915100 AS left_time, 1496921700 AS right_time UNION ALL
SELECT 92 AS gap_no, 1496922000 AS left_time, 1496926500 AS right_time UNION ALL
SELECT 93 AS gap_no, 1497130800 AS left_time, 1497136500 AS right_time UNION ALL
SELECT 94 AS gap_no, 1497166200 AS left_time, 1497178200 AS right_time UNION ALL
SELECT 95 AS gap_no, 1497258600 AS left_time, 1497262500 AS right_time UNION ALL
SELECT 96 AS gap_no, 1497281400 AS left_time, 1497285900 AS right_time UNION ALL
SELECT 97 AS gap_no, 1497309300 AS left_time, 1497318600 AS right_time UNION ALL
SELECT 98 AS gap_no, 1497337200 AS left_time, 1497342300 AS right_time UNION ALL
SELECT 99 AS gap_no, 1497350100 AS left_time, 1497357000 AS right_time UNION ALL
SELECT 100 AS gap_no, 1497507000 AS left_time, 1497511200 AS right_time UNION ALL
SELECT 101 AS gap_no, 1497515700 AS left_time, 1497519900 AS right_time UNION ALL
SELECT 102 AS gap_no, 1497519900 AS left_time, 1497524100 AS right_time UNION ALL
SELECT 103 AS gap_no, 1497524400 AS left_time, 1497540300 AS right_time UNION ALL
SELECT 104 AS gap_no, 1497540600 AS left_time, 1497558300 AS right_time UNION ALL
SELECT 105 AS gap_no, 1497617700 AS left_time, 1497628200 AS right_time UNION ALL
SELECT 106 AS gap_no, 1497628500 AS left_time, 1497634500 AS right_time UNION ALL
SELECT 107 AS gap_no, 1497641400 AS left_time, 1497645900 AS right_time UNION ALL
SELECT 108 AS gap_no, 1497671700 AS left_time, 1497685200 AS right_time UNION ALL
SELECT 109 AS gap_no, 1497705300 AS left_time, 1497718800 AS right_time UNION ALL
SELECT 110 AS gap_no, 1497719400 AS left_time, 1497723900 AS right_time UNION ALL
SELECT 111 AS gap_no, 1497724500 AS left_time, 1497741600 AS right_time UNION ALL
SELECT 112 AS gap_no, 1497742200 AS left_time, 1497759600 AS right_time UNION ALL
SELECT 113 AS gap_no, 1497781800 AS left_time, 1497788700 AS right_time UNION ALL
SELECT 114 AS gap_no, 1497789000 AS left_time, 1497793500 AS right_time UNION ALL
SELECT 115 AS gap_no, 1497802200 AS left_time, 1497821100 AS right_time UNION ALL
SELECT 116 AS gap_no, 1497828600 AS left_time, 1497839700 AS right_time UNION ALL
SELECT 117 AS gap_no, 1497849000 AS left_time, 1497853200 AS right_time UNION ALL
SELECT 118 AS gap_no, 1497853500 AS left_time, 1497857100 AS right_time UNION ALL
SELECT 119 AS gap_no, 1497861600 AS left_time, 1497867300 AS right_time UNION ALL
SELECT 120 AS gap_no, 1497867900 AS left_time, 1497871500 AS right_time UNION ALL
SELECT 121 AS gap_no, 1498070400 AS left_time, 1498074300 AS right_time UNION ALL
SELECT 122 AS gap_no, 1498305300 AS left_time, 1498311000 AS right_time UNION ALL
SELECT 123 AS gap_no, 1498321800 AS left_time, 1498327200 AS right_time UNION ALL
SELECT 124 AS gap_no, 1498660200 AS left_time, 1498672200 AS right_time UNION ALL
SELECT 125 AS gap_no, 1498715700 AS left_time, 1498719300 AS right_time UNION ALL
SELECT 126 AS gap_no, 1498744500 AS left_time, 1498750500 AS right_time UNION ALL
SELECT 127 AS gap_no, 1498754100 AS left_time, 1498761600 AS right_time UNION ALL
SELECT 128 AS gap_no, 1498761900 AS left_time, 1498772100 AS right_time UNION ALL
SELECT 129 AS gap_no, 1498851900 AS left_time, 1498856100 AS right_time UNION ALL
SELECT 130 AS gap_no, 1498898100 AS left_time, 1498905300 AS right_time UNION ALL
SELECT 131 AS gap_no, 1498923900 AS left_time, 1498928100 AS right_time UNION ALL
SELECT 132 AS gap_no, 1499314200 AS left_time, 1499317800 AS right_time UNION ALL
SELECT 133 AS gap_no, 1499355300 AS left_time, 1499360400 AS right_time UNION ALL
SELECT 134 AS gap_no, 1499426100 AS left_time, 1499429700 AS right_time UNION ALL
SELECT 135 AS gap_no, 1499439000 AS left_time, 1499459100 AS right_time UNION ALL
SELECT 136 AS gap_no, 1499459700 AS left_time, 1499472900 AS right_time UNION ALL
SELECT 137 AS gap_no, 1499473200 AS left_time, 1499477700 AS right_time UNION ALL
SELECT 138 AS gap_no, 1499490000 AS left_time, 1499503200 AS right_time UNION ALL
SELECT 139 AS gap_no, 1499566500 AS left_time, 1499570100 AS right_time UNION ALL
SELECT 140 AS gap_no, 1499662500 AS left_time, 1499668500 AS right_time UNION ALL
SELECT 141 AS gap_no, 1499727300 AS left_time, 1499734500 AS right_time UNION ALL
SELECT 142 AS gap_no, 1499829600 AS left_time, 1499846400 AS right_time UNION ALL
SELECT 143 AS gap_no, 1500023700 AS left_time, 1500031500 AS right_time UNION ALL
SELECT 144 AS gap_no, 1500032400 AS left_time, 1500036000 AS right_time UNION ALL
SELECT 145 AS gap_no, 1500036600 AS left_time, 1500042600 AS right_time UNION ALL
SELECT 146 AS gap_no, 1500108000 AS left_time, 1500114300 AS right_time UNION ALL
SELECT 147 AS gap_no, 1500582600 AS left_time, 1500587400 AS right_time UNION ALL
SELECT 148 AS gap_no, 1500588000 AS left_time, 1500593100 AS right_time UNION ALL
SELECT 149 AS gap_no, 1500595800 AS left_time, 1500603300 AS right_time UNION ALL
SELECT 150 AS gap_no, 1500635400 AS left_time, 1500650100 AS right_time UNION ALL
SELECT 151 AS gap_no, 1500652500 AS left_time, 1500662400 AS right_time UNION ALL
SELECT 152 AS gap_no, 1500662700 AS left_time, 1500670200 AS right_time UNION ALL
SELECT 153 AS gap_no, 1500671400 AS left_time, 1500745500 AS right_time UNION ALL
SELECT 154 AS gap_no, 1500810900 AS left_time, 1500815700 AS right_time UNION ALL
SELECT 155 AS gap_no, 1500984900 AS left_time, 1500990000 AS right_time UNION ALL
SELECT 156 AS gap_no, 1501013400 AS left_time, 1501062900 AS right_time UNION ALL
SELECT 157 AS gap_no, 1501087500 AS left_time, 1501091700 AS right_time UNION ALL
SELECT 158 AS gap_no, 1501101300 AS left_time, 1501108800 AS right_time UNION ALL
SELECT 159 AS gap_no, 1501109100 AS left_time, 1501124100 AS right_time UNION ALL
SELECT 160 AS gap_no, 1501125000 AS left_time, 1501129200 AS right_time UNION ALL
SELECT 161 AS gap_no, 1501180500 AS left_time, 1501185000 AS right_time UNION ALL
SELECT 162 AS gap_no, 1501248900 AS left_time, 1501262700 AS right_time UNION ALL
SELECT 163 AS gap_no, 1501263900 AS left_time, 1501276200 AS right_time UNION ALL
SELECT 164 AS gap_no, 1501276500 AS left_time, 1501311300 AS right_time UNION ALL
SELECT 165 AS gap_no, 1501312500 AS left_time, 1501318500 AS right_time UNION ALL
SELECT 166 AS gap_no, 1501337700 AS left_time, 1501344000 AS right_time UNION ALL
SELECT 167 AS gap_no, 1501346400 AS left_time, 1501353600 AS right_time UNION ALL
SELECT 168 AS gap_no, 1501477800 AS left_time, 1501514400 AS right_time UNION ALL
SELECT 169 AS gap_no, 1501796100 AS left_time, 1501803000 AS right_time UNION ALL
SELECT 170 AS gap_no, 1501812600 AS left_time, 1501816500 AS right_time UNION ALL
SELECT 171 AS gap_no, 1502088000 AS left_time, 1502093400 AS right_time UNION ALL
SELECT 172 AS gap_no, 1502107500 AS left_time, 1502112300 AS right_time UNION ALL
SELECT 173 AS gap_no, 1502131200 AS left_time, 1502137200 AS right_time UNION ALL
SELECT 174 AS gap_no, 1502147100 AS left_time, 1502154900 AS right_time UNION ALL
SELECT 175 AS gap_no, 1502155800 AS left_time, 1502163600 AS right_time UNION ALL
SELECT 176 AS gap_no, 1502165700 AS left_time, 1502172000 AS right_time UNION ALL
SELECT 177 AS gap_no, 1502188800 AS left_time, 1502195700 AS right_time UNION ALL
SELECT 178 AS gap_no, 1502660400 AS left_time, 1502667000 AS right_time UNION ALL
SELECT 179 AS gap_no, 1502667300 AS left_time, 1502670900 AS right_time UNION ALL
SELECT 180 AS gap_no, 1502671500 AS left_time, 1502686800 AS right_time UNION ALL
SELECT 181 AS gap_no, 1502743500 AS left_time, 1502750400 AS right_time UNION ALL
SELECT 182 AS gap_no, 1502752800 AS left_time, 1502757000 AS right_time UNION ALL
SELECT 183 AS gap_no, 1502775600 AS left_time, 1502779500 AS right_time UNION ALL
SELECT 184 AS gap_no, 1502779800 AS left_time, 1502795700 AS right_time UNION ALL
SELECT 185 AS gap_no, 1502810700 AS left_time, 1502816400 AS right_time UNION ALL
SELECT 186 AS gap_no, 1502820600 AS left_time, 1502832000 AS right_time UNION ALL
SELECT 187 AS gap_no, 1502842200 AS left_time, 1502847600 AS right_time UNION ALL
SELECT 188 AS gap_no, 1502847900 AS left_time, 1502852400 AS right_time UNION ALL
SELECT 189 AS gap_no, 1502862300 AS left_time, 1502868600 AS right_time UNION ALL
SELECT 190 AS gap_no, 1503897000 AS left_time, 1503910200 AS right_time UNION ALL
SELECT 191 AS gap_no, 1503913200 AS left_time, 1503920400 AS right_time UNION ALL
SELECT 192 AS gap_no, 1503943200 AS left_time, 1503949200 AS right_time UNION ALL
SELECT 193 AS gap_no, 1504057800 AS left_time, 1504061400 AS right_time UNION ALL
SELECT 194 AS gap_no, 1504977600 AS left_time, 1505001600 AS right_time UNION ALL
SELECT 195 AS gap_no, 1505005200 AS left_time, 1505010000 AS right_time UNION ALL
SELECT 196 AS gap_no, 1505010300 AS left_time, 1505018700 AS right_time UNION ALL
SELECT 197 AS gap_no, 1505027400 AS left_time, 1505035200 AS right_time UNION ALL
SELECT 198 AS gap_no, 1505035500 AS left_time, 1505043600 AS right_time UNION ALL
SELECT 199 AS gap_no, 1505044500 AS left_time, 1505058900 AS right_time UNION ALL
SELECT 200 AS gap_no, 1505060400 AS left_time, 1505065500 AS right_time UNION ALL
SELECT 201 AS gap_no, 1505074200 AS left_time, 1505078400 AS right_time UNION ALL
SELECT 202 AS gap_no, 1505889600 AS left_time, 1505895300 AS right_time UNION ALL
SELECT 203 AS gap_no, 1505995800 AS left_time, 1505999700 AS right_time UNION ALL
SELECT 204 AS gap_no, 1506020400 AS left_time, 1506025200 AS right_time UNION ALL
SELECT 205 AS gap_no, 1506273600 AS left_time, 1506297000 AS right_time UNION ALL
SELECT 206 AS gap_no, 1506297300 AS left_time, 1506303000 AS right_time UNION ALL
SELECT 207 AS gap_no, 1506974100 AS left_time, 1506978600 AS right_time UNION ALL
SELECT 208 AS gap_no, 1506978900 AS left_time, 1506987600 AS right_time UNION ALL
SELECT 209 AS gap_no, 1506993000 AS left_time, 1506996900 AS right_time UNION ALL
SELECT 210 AS gap_no, 1507488900 AS left_time, 1507492800 AS right_time UNION ALL
SELECT 211 AS gap_no, 1507498800 AS left_time, 1507509600 AS right_time UNION ALL
SELECT 212 AS gap_no, 1507512300 AS left_time, 1507516500 AS right_time UNION ALL
SELECT 213 AS gap_no, 1507528800 AS left_time, 1507537500 AS right_time UNION ALL
SELECT 214 AS gap_no, 1507537800 AS left_time, 1507562400 AS right_time UNION ALL
SELECT 215 AS gap_no, 1507623000 AS left_time, 1507626900 AS right_time UNION ALL
SELECT 216 AS gap_no, 1507627500 AS left_time, 1507643700 AS right_time UNION ALL
SELECT 217 AS gap_no, 1508010600 AS left_time, 1508015700 AS right_time UNION ALL
SELECT 218 AS gap_no, 1508048100 AS left_time, 1508052000 AS right_time UNION ALL
SELECT 219 AS gap_no, 1508388300 AS left_time, 1508396400 AS right_time UNION ALL
SELECT 220 AS gap_no, 1508396700 AS left_time, 1508400900 AS right_time UNION ALL
SELECT 221 AS gap_no, 1509567600 AS left_time, 1509572400 AS right_time UNION ALL
SELECT 222 AS gap_no, 1509572700 AS left_time, 1509579000 AS right_time UNION ALL
SELECT 223 AS gap_no, 1509579300 AS left_time, 1509587400 AS right_time UNION ALL
SELECT 224 AS gap_no, 1509591000 AS left_time, 1509597000 AS right_time UNION ALL
SELECT 225 AS gap_no, 1509758700 AS left_time, 1509762600 AS right_time UNION ALL
SELECT 226 AS gap_no, 1509945600 AS left_time, 1509957900 AS right_time UNION ALL
SELECT 227 AS gap_no, 1510347300 AS left_time, 1510384500 AS right_time UNION ALL
SELECT 228 AS gap_no, 1510392300 AS left_time, 1510398900 AS right_time UNION ALL
SELECT 229 AS gap_no, 1510442100 AS left_time, 1510445700 AS right_time UNION ALL
SELECT 230 AS gap_no, 1510560000 AS left_time, 1510565100 AS right_time UNION ALL
SELECT 231 AS gap_no, 1511100600 AS left_time, 1511104800 AS right_time UNION ALL
SELECT 232 AS gap_no, 1511151600 AS left_time, 1511156100 AS right_time UNION ALL
SELECT 233 AS gap_no, 1511193600 AS left_time, 1511197200 AS right_time UNION ALL
SELECT 234 AS gap_no, 1511213100 AS left_time, 1511224800 AS right_time UNION ALL
SELECT 235 AS gap_no, 1511225100 AS left_time, 1511231400 AS right_time UNION ALL
SELECT 236 AS gap_no, 1511248200 AS left_time, 1511256300 AS right_time UNION ALL
SELECT 237 AS gap_no, 1511256900 AS left_time, 1511272200 AS right_time UNION ALL
SELECT 238 AS gap_no, 1511275800 AS left_time, 1511281200 AS right_time UNION ALL
SELECT 239 AS gap_no, 1511347800 AS left_time, 1511352600 AS right_time UNION ALL
SELECT 240 AS gap_no, 1511459400 AS left_time, 1511464500 AS right_time UNION ALL
SELECT 241 AS gap_no, 1511467800 AS left_time, 1511472900 AS right_time UNION ALL
SELECT 242 AS gap_no, 1511492100 AS left_time, 1511495700 AS right_time UNION ALL
SELECT 243 AS gap_no, 1512057300 AS left_time, 1512060900 AS right_time UNION ALL
SELECT 244 AS gap_no, 1512073500 AS left_time, 1512077100 AS right_time UNION ALL
SELECT 245 AS gap_no, 1512078900 AS left_time, 1512085500 AS right_time UNION ALL
SELECT 246 AS gap_no, 1512103500 AS left_time, 1512113700 AS right_time UNION ALL
SELECT 247 AS gap_no, 1512114000 AS left_time, 1512151200 AS right_time UNION ALL
SELECT 248 AS gap_no, 1512300000 AS left_time, 1512305100 AS right_time UNION ALL
SELECT 249 AS gap_no, 1512388800 AS left_time, 1512392400 AS right_time UNION ALL
SELECT 250 AS gap_no, 1512392400 AS left_time, 1512417300 AS right_time UNION ALL
SELECT 251 AS gap_no, 1512452100 AS left_time, 1512489300 AS right_time UNION ALL
SELECT 252 AS gap_no, 1512545700 AS left_time, 1512555300 AS right_time UNION ALL
SELECT 253 AS gap_no, 1512558300 AS left_time, 1512562500 AS right_time UNION ALL
SELECT 254 AS gap_no, 1512719100 AS left_time, 1512768900 AS right_time UNION ALL
SELECT 255 AS gap_no, 1512810600 AS left_time, 1512860100 AS right_time UNION ALL
SELECT 256 AS gap_no, 1512956100 AS left_time, 1513005900 AS right_time UNION ALL
SELECT 257 AS gap_no, 1513344000 AS left_time, 1513356300 AS right_time UNION ALL
SELECT 258 AS gap_no, 1513356600 AS left_time, 1513361700 AS right_time UNION ALL
SELECT 259 AS gap_no, 1513362000 AS left_time, 1513367700 AS right_time UNION ALL
SELECT 260 AS gap_no, 1513459800 AS left_time, 1513464300 AS right_time UNION ALL
SELECT 261 AS gap_no, 1513474800 AS left_time, 1513479600 AS right_time UNION ALL
SELECT 262 AS gap_no, 1513520100 AS left_time, 1513594200 AS right_time UNION ALL
SELECT 263 AS gap_no, 1513626000 AS left_time, 1513689600 AS right_time
), source_keys AS (
 SELECT g.gap_no,a.dateTime FROM gaps g JOIN old_weewx.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
 UNION
 SELECT g.gap_no,a.dateTime FROM gaps g JOIN weewx_WH1080.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
)
SELECT
 g.gap_no,
 g.left_time,
 g.right_time,
 COUNT(k.dateTime) AS source_union_timestamps,
 SUM(o.dateTime IS NOT NULL) AS old_rows,
 SUM(w.dateTime IS NOT NULL) AS wh1080_rows,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL) AS exact_timestamp_pairs,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NULL) AS old_only_timestamps,
 SUM(o.dateTime IS NULL AND w.dateTime IS NOT NULL) AS wh1080_only_timestamps,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND (o.usUnits<>w.usUnits OR o.interval<>w.interval)) AS unit_interval_conflicts,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL) AS `outTemp_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`=w.`outTemp`) AS `outTemp_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`<>w.`outTemp`) AS `outTemp_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`outTemp` IS NULL)<>(w.`outTemp` IS NULL))) AS `outTemp_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL) AS `outHumidity_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`=w.`outHumidity`) AS `outHumidity_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`<>w.`outHumidity`) AS `outHumidity_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`outHumidity` IS NULL)<>(w.`outHumidity` IS NULL))) AS `outHumidity_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL) AS `rain_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`=w.`rain`) AS `rain_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`<>w.`rain`) AS `rain_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`rain` IS NULL)<>(w.`rain` IS NULL))) AS `rain_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL) AS `rainRate_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`=w.`rainRate`) AS `rainRate_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`<>w.`rainRate`) AS `rainRate_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`rainRate` IS NULL)<>(w.`rainRate` IS NULL))) AS `rainRate_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL) AS `windSpeed_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`=w.`windSpeed`) AS `windSpeed_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`<>w.`windSpeed`) AS `windSpeed_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windSpeed` IS NULL)<>(w.`windSpeed` IS NULL))) AS `windSpeed_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL) AS `windGust_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`=w.`windGust`) AS `windGust_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`<>w.`windGust`) AS `windGust_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windGust` IS NULL)<>(w.`windGust` IS NULL))) AS `windGust_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL) AS `windDir_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`=w.`windDir`) AS `windDir_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`<>w.`windDir`) AS `windDir_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windDir` IS NULL)<>(w.`windDir` IS NULL))) AS `windDir_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL) AS `pressure_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`=w.`pressure`) AS `pressure_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`<>w.`pressure`) AS `pressure_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`pressure` IS NULL)<>(w.`pressure` IS NULL))) AS `pressure_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL) AS `barometer_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`=w.`barometer`) AS `barometer_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`<>w.`barometer`) AS `barometer_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`barometer` IS NULL)<>(w.`barometer` IS NULL))) AS `barometer_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL) AS `altimeter_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`=w.`altimeter`) AS `altimeter_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`<>w.`altimeter`) AS `altimeter_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`altimeter` IS NULL)<>(w.`altimeter` IS NULL))) AS `altimeter_null_asymmetry`
FROM gaps g LEFT JOIN source_keys k ON k.gap_no=g.gap_no
LEFT JOIN old_weewx.archive o ON o.dateTime=k.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=k.dateTime
GROUP BY g.gap_no,g.left_time,g.right_time ORDER BY g.gap_no;
