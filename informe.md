# Backtest de las señales

Generado: 2026-11-11 14:53 UTC · Monedas: BTCUSDT, ETHUSDT · Datos: Binance (velas cerradas).

**Cómo leerlo.** Cada celda es la *ventaja* de la señal: lo que se movió el precio a favor de la señal, menos lo que se habría movido eligiendo velas al azar con el mismo sentido. `n` = veces que apareció la señal, `acierta` = % de veces que el precio fue en el sentido esperado, `p` = probabilidad de que el azar lo iguale (✅ si p ≤ 0,05 a favor; ❌ si la señal va claramente al revés). «Fuera de muestra» = solo el último 40 % del histórico.

En las señales de agotamiento y salida el sentido esperado es CONTRA la tendencia; en las «zonas no operables» se mide qué pasa si compras ahí (lo esperable es ventaja negativa).

## Temporalidad 4h

Velas evaluadas — BTCUSDT: 20095, ETHUSDT: 20095

| Señal | a 5 velas | a 10 velas | a 20 velas | fuera de muestra (horizonte medio) |
|---|---|---|---|---|
| Tendencia «sana» (se espera que siga) | +0,27 % (n=1033, acierta 54,0 %, p=0,019) ✅ | +0,52 % (n=1033, acierta 53,0 %, p=0,01) ✅ | +0,78 % (n=1031, acierta 51,3 %, p=0,008) ✅ | -0,04 % (n=360, acierta 47,8 %, p=0,5944) |
| Tendencia «agotándose» (≥2 de 4 señales) | -0,45 % (n=506, acierta 48,0 %, p=0,991) ❌ | -0,59 % (n=506, acierta 46,4 %, p=0,984) ❌ | -0,97 % (n=506, acierta 46,6 %, p=0,981) ❌ | +0,17 % (n=161, acierta 50,3 %, p=0,3027) |
| Agotamiento con ≥3 de 4 señales | -0,29 % (n=57, acierta 45,6 %, p=0,7243) | -0,86 % (n=57, acierta 49,1 %, p=0,8731) | -1,00 % (n=57, acierta 47,4 %, p=0,8082) | -0,71 % (n=15, acierta 46,7 %, p=0,7822) |
| Al menos 1 señal de agotamiento | -0,16 % (n=884, acierta 46,8 %, p=0,8891) | -0,29 % (n=884, acierta 50,3 %, p=0,9211) | -0,41 % (n=883, acierta 49,7 %, p=0,8871) | -0,00 % (n=319, acierta 50,5 %, p=0,5095) |
| Agotamiento: divergencia | -0,08 % (n=324, acierta 47,2 %, p=0,6553) | -0,26 % (n=324, acierta 53,1 %, p=0,8122) | -0,75 % (n=323, acierta 48,0 %, p=0,9481) | -0,11 % (n=119, acierta 53,8 %, p=0,6384) |
| Agotamiento: doble techo/suelo | -0,51 % (n=275, acierta 43,3 %, p=0,988) ❌ | -0,72 % (n=275, acierta 46,2 %, p=0,982) ❌ | -0,84 % (n=274, acierta 47,8 %, p=0,954) ❌ | +0,16 % (n=98, acierta 43,9 %, p=0,3377) |
| Agotamiento: medias 10/55 juntándose | -0,29 % (n=349, acierta 47,0 %, p=0,9091) | -0,48 % (n=349, acierta 46,1 %, p=0,9431) | -0,36 % (n=349, acierta 47,6 %, p=0,7772) | -0,01 % (n=126, acierta 49,2 %, p=0,5025) |
| Agotamiento: ADX cede | -0,15 % (n=614, acierta 50,0 %, p=0,8252) | -0,22 % (n=614, acierta 50,2 %, p=0,8162) | -0,39 % (n=614, acierta 49,5 %, p=0,8581) | +0,15 % (n=194, acierta 52,6 %, p=0,3367) |
| Divergencia (RSI o Squeeze) | -0,03 % (n=715, acierta 53,3 %, p=0,5784) | -0,06 % (n=715, acierta 52,9 %, p=0,6184) | -0,09 % (n=713, acierta 51,1 %, p=0,6234) | -0,06 % (n=290, acierta 50,0 %, p=0,6154) |
| Divergencia solo en RSI | -0,24 % (n=239, acierta 50,2 %, p=0,8452) | -0,43 % (n=239, acierta 52,3 %, p=0,9101) | -0,74 % (n=239, acierta 48,1 %, p=0,951) ❌ | -0,41 % (n=93, acierta 49,5 %, p=0,8701) |
| Divergencia solo en Squeeze | -0,12 % (n=333, acierta 52,9 %, p=0,7413) | +0,03 % (n=333, acierta 52,3 %, p=0,4695) | +0,33 % (n=331, acierta 51,4 %, p=0,2008) | +0,51 % (n=132, acierta 55,3 %, p=0,0559) |
| Divergencia en RSI y Squeeze a la vez | +0,27 % (n=235, acierta 55,3 %, p=0,1339) | +0,17 % (n=235, acierta 55,3 %, p=0,3057) | +0,02 % (n=235, acierta 51,9 %, p=0,4905) | -0,65 % (n=102, acierta 45,1 %, p=0,967) ❌ |
| Divergencia + ADX con pendiente negativa (aviso reforzado) | -0,05 % (n=1064, acierta 51,5 %, p=0,7003) | -0,12 % (n=1064, acierta 51,6 %, p=0,7463) | -0,03 % (n=1063, acierta 50,6 %, p=0,5485) | -0,13 % (n=418, acierta 50,5 %, p=0,7742) |
| Divergencia con ADX subiendo | +0,03 % (n=867, acierta 52,4 %, p=0,4066) | -0,07 % (n=867, acierta 53,5 %, p=0,6503) | +0,19 % (n=865, acierta 53,5 %, p=0,2727) | -0,20 % (n=367, acierta 49,9 %, p=0,8172) |
| Ruptura de lateral confirmada | +0,34 % (n=394, acierta 52,5 %, p=0,049) ✅ | +0,53 % (n=394, acierta 51,3 %, p=0,025) ✅ | +0,72 % (n=394, acierta 52,8 %, p=0,037) ✅ | -0,10 % (n=178, acierta 42,7 %, p=0,6394) |
| Posible ruptura (sin confirmar) | +0,32 % (n=951, acierta 47,3 %, p=0,006) ✅ | +0,14 % (n=951, acierta 46,8 %, p=0,2168) | -0,06 % (n=951, acierta 47,0 %, p=0,5794) | -0,03 % (n=384, acierta 44,8 %, p=0,5654) |
| Entrada long: 4 de 4 condiciones | -0,12 % (n=651, acierta 49,9 %, p=0,7952) | -0,15 % (n=651, acierta 50,7 %, p=0,7692) | -0,03 % (n=651, acierta 50,5 %, p=0,5355) | -0,06 % (n=280, acierta 50,7 %, p=0,5974) |
| Entrada long 4/4 y ninguna zona no operable | -0,27 % (n=413, acierta 49,6 %, p=0,9211) | -0,33 % (n=413, acierta 49,4 %, p=0,8751) | -0,59 % (n=413, acierta 49,2 %, p=0,9261) | -0,29 % (n=150, acierta 48,0 %, p=0,8302) |
| Entrada long: ≥3 de 4 condiciones | -0,04 % (n=2285, acierta 49,9 %, p=0,7083) | -0,09 % (n=2285, acierta 49,6 %, p=0,7922) | -0,01 % (n=2284, acierta 51,1 %, p=0,4955) | -0,01 % (n=925, acierta 48,4 %, p=0,5235) |
| Entrada: precio en la EMA 55 / parte baja | -0,07 % (n=2688, acierta 50,5 %, p=0,8272) | -0,12 % (n=2688, acierta 50,6 %, p=0,9011) | -0,04 % (n=2688, acierta 50,3 %, p=0,5924) | -0,27 % (n=1136, acierta 48,8 %, p=0,996) ❌ |
| Entrada: Squeeze en valle rojo girando | +0,08 % (n=1815, acierta 52,6 %, p=0,1728) | +0,04 % (n=1815, acierta 52,5 %, p=0,3686) | +0,09 % (n=1812, acierta 54,1 %, p=0,2797) | +0,05 % (n=716, acierta 53,1 %, p=0,3457) |
| Entrada: ADX con pendiente negativa | +0,02 % (n=2627, acierta 50,7 %, p=0,4036) | +0,00 % (n=2627, acierta 51,8 %, p=0,4855) | +0,08 % (n=2625, acierta 51,8 %, p=0,2278) | -0,02 % (n=1044, acierta 49,2 %, p=0,5924) |
| Entrada: cerca del POC aproximado | -0,05 % (n=2262, acierta 50,6 %, p=0,7502) | -0,10 % (n=2262, acierta 50,7 %, p=0,8192) | -0,03 % (n=2262, acierta 50,9 %, p=0,5734) | -0,14 % (n=948, acierta 49,1 %, p=0,8951) |
| Zona no operable: mitad del lateral (comprando) | -0,02 % (n=1764, acierta 52,2 %, p=0,6014) | -0,08 % (n=1764, acierta 51,2 %, p=0,7303) | -0,04 % (n=1764, acierta 52,7 %, p=0,5744) | -0,02 % (n=765, acierta 48,9 %, p=0,5714) |
| Zona no operable: topado / sobreextendido (comprando) | +0,36 % (n=1320, acierta 52,1 %, p=0,003) ✅ | +0,48 % (n=1320, acierta 52,3 %, p=0,005) ✅ | +0,57 % (n=1320, acierta 50,5 %, p=0,015) ✅ | +0,11 % (n=493, acierta 47,9 %, p=0,2458) |
| Zona no operable: caída con ADX subiendo (comprando) | -0,15 % (n=2549, acierta 52,8 %, p=0,987) ❌ | -0,27 % (n=2546, acierta 53,1 %, p=0,999) ❌ | -0,20 % (n=2544, acierta 53,0 %, p=0,9471) | -0,32 % (n=1056, acierta 51,8 %, p=0,999) ❌ |
| Salida: ≥2 de 3 condiciones | -0,30 % (n=399, acierta 50,9 %, p=0,9311) | -0,48 % (n=399, acierta 51,6 %, p=0,9441) | -0,63 % (n=399, acierta 49,6 %, p=0,9181) | +0,10 % (n=168, acierta 56,5 %, p=0,3816) |
| Salida: parte alta del rango | -0,32 % (n=1403, acierta 49,4 %, p=0,997) ❌ | -0,39 % (n=1403, acierta 48,8 %, p=0,992) ❌ | -0,54 % (n=1403, acierta 48,2 %, p=0,987) ❌ | +0,02 % (n=544, acierta 53,5 %, p=0,4745) |
| Salida: divergencia bajista en Squeeze | +0,01 % (n=299, acierta 53,5 %, p=0,4915) | -0,04 % (n=299, acierta 50,2 %, p=0,5644) | +0,32 % (n=299, acierta 49,2 %, p=0,2088) | -0,23 % (n=119, acierta 47,1 %, p=0,7592) |
| Salida: pérdida de volatilidad tras impulso | -0,14 % (n=608, acierta 47,9 %, p=0,8112) | -0,21 % (n=608, acierta 49,0 %, p=0,8232) | -0,62 % (n=608, acierta 46,1 %, p=0,9471) | +0,01 % (n=284, acierta 50,7 %, p=0,4795) |
| Nota de la temporalidad ≥ 7,5 (score ≥ 0,5) | +0,51 % (n=1298, acierta 52,6 %, p=0,003) ✅ | +0,58 % (n=1298, acierta 53,6 %, p=0,006) ✅ | +1,09 % (n=1298, acierta 54,9 %, p=0,006) ✅ | +0,36 % (n=531, acierta 50,7 %, p=0,023) ✅ |
| Nota de la temporalidad ≤ 2,5 (score ≤ −0,5) | +0,14 % (n=1244, acierta 44,9 %, p=0,0829) | +0,05 % (n=1242, acierta 44,8 %, p=0,3726) | +0,35 % (n=1240, acierta 45,0 %, p=0,1059) | +0,06 % (n=494, acierta 44,1 %, p=0,3766) |

## Temporalidad 1d

Velas evaluadas — BTCUSDT: 3244, ETHUSDT: 3244

| Señal | a 5 velas | a 10 velas | a 20 velas | fuera de muestra (horizonte medio) |
|---|---|---|---|---|
| Tendencia «sana» (se espera que siga) | +0,79 % (n=197, acierta 55,8 %, p=0,1159) | +1,32 % (n=196, acierta 50,5 %, p=0,1359) | +1,82 % (n=195, acierta 52,8 %, p=0,1389) | +0,93 % (n=70, acierta 54,3 %, p=0,2368) |
| Tendencia «agotándose» (≥2 de 4 señales) | +0,09 % (n=104, acierta 51,0 %, p=0,4675) | +0,05 % (n=103, acierta 51,5 %, p=0,4865) | -0,95 % (n=103, acierta 59,2 %, p=0,6573) | +0,84 % (n=49, acierta 49,0 %, p=0,3187) |
| Agotamiento con ≥3 de 4 señales | -0,69 % (n=19, acierta 47,4 %, p=0,6084) | -0,26 % (n=19, acierta 52,6 %, p=0,5335) | -3,38 % (n=19, acierta 57,9 %, p=0,7093) | +1,08 % (n=10, acierta 60,0 %, p=0,3786) |
| Al menos 1 señal de agotamiento | +0,70 % (n=171, acierta 55,6 %, p=0,1558) | +0,96 % (n=170, acierta 48,2 %, p=0,2178) | +0,14 % (n=169, acierta 52,7 %, p=0,4735) | -1,39 % (n=61, acierta 41,0 %, p=0,8452) |
| Agotamiento: divergencia | +0,39 % (n=60, acierta 60,0 %, p=0,3906) | -0,20 % (n=60, acierta 51,7 %, p=0,5405) | -1,23 % (n=60, acierta 56,7 %, p=0,6793) | -0,23 % (n=20, acierta 55,0 %, p=0,5574) |
| Agotamiento: doble techo/suelo | -0,35 % (n=58, acierta 53,4 %, p=0,6284) | +0,04 % (n=58, acierta 41,4 %, p=0,5015) | -0,02 % (n=58, acierta 53,4 %, p=0,5025) | -0,96 % (n=29, acierta 31,0 %, p=0,6993) |
| Agotamiento: medias 10/55 juntándose | +0,99 % (n=74, acierta 54,1 %, p=0,2048) | +1,49 % (n=73, acierta 56,2 %, p=0,1998) | +0,47 % (n=72, acierta 55,6 %, p=0,4316) | -2,10 % (n=27, acierta 44,4 %, p=0,8511) |
| Agotamiento: ADX cede | +0,38 % (n=117, acierta 52,1 %, p=0,3317) | +0,67 % (n=116, acierta 49,1 %, p=0,3127) | -1,13 % (n=116, acierta 55,2 %, p=0,7063) | +1,27 % (n=52, acierta 53,8 %, p=0,2058) |
| Divergencia (RSI o Squeeze) | -0,28 % (n=112, acierta 51,8 %, p=0,6334) | -0,81 % (n=112, acierta 43,8 %, p=0,7483) | -1,59 % (n=112, acierta 52,7 %, p=0,8172) | -0,46 % (n=50, acierta 48,0 %, p=0,6494) |
| Divergencia solo en RSI | -0,18 % (n=44, acierta 54,5 %, p=0,5694) | -1,78 % (n=44, acierta 43,2 %, p=0,8112) | -4,48 % (n=44, acierta 40,9 %, p=0,9461) | -1,88 % (n=20, acierta 40,0 %, p=0,8222) |
| Divergencia solo en Squeeze | -1,20 % (n=62, acierta 43,5 %, p=0,8601) | -0,59 % (n=61, acierta 44,3 %, p=0,6424) | -0,86 % (n=61, acierta 54,1 %, p=0,6553) | -1,83 % (n=26, acierta 42,3 %, p=0,8591) |
| Divergencia en RSI y Squeeze a la vez | +0,63 % (n=30, acierta 53,3 %, p=0,3277) | +0,20 % (n=30, acierta 43,3 %, p=0,4805) | -0,01 % (n=30, acierta 60,0 %, p=0,5255) | +2,57 % (n=15, acierta 60,0 %, p=0,1439) |
| Divergencia + ADX con pendiente negativa (aviso reforzado) | -0,28 % (n=178, acierta 49,4 %, p=0,6583) | -1,41 % (n=176, acierta 44,9 %, p=0,8971) | -1,21 % (n=174, acierta 52,9 %, p=0,7642) | -1,06 % (n=80, acierta 42,5 %, p=0,8122) |
| Divergencia con ADX subiendo | +0,03 % (n=151, acierta 55,6 %, p=0,4965) | -0,52 % (n=151, acierta 50,3 %, p=0,6893) | -1,63 % (n=147, acierta 48,3 %, p=0,8122) | +1,71 % (n=69, acierta 52,2 %, p=0,0899) |
| Ruptura de lateral confirmada | +0,34 % (n=54, acierta 48,1 %, p=0,3716) | +0,47 % (n=54, acierta 53,7 %, p=0,4046) | +2,44 % (n=53, acierta 66,0 %, p=0,1868) | -0,54 % (n=24, acierta 50,0 %, p=0,6214) |
| Posible ruptura (sin confirmar) | +0,99 % (n=141, acierta 50,4 %, p=0,0989) | +1,93 % (n=140, acierta 50,7 %, p=0,0519) | +3,91 % (n=139, acierta 61,9 %, p=0,02) ✅ | +0,80 % (n=66, acierta 50,0 %, p=0,2358) |
| Entrada long: 4 de 4 condiciones | -0,38 % (n=86, acierta 44,2 %, p=0,6474) | -0,37 % (n=85, acierta 51,8 %, p=0,5934) | -0,77 % (n=85, acierta 50,6 %, p=0,6164) | +1,61 % (n=45, acierta 53,3 %, p=0,1618) |
| Entrada long 4/4 y ninguna zona no operable | -0,24 % (n=61, acierta 42,6 %, p=0,5754) | -1,07 % (n=61, acierta 45,9 %, p=0,6913) | -2,61 % (n=61, acierta 44,3 %, p=0,8042) | +1,49 % (n=32, acierta 50,0 %, p=0,2567) |
| Entrada long: ≥3 de 4 condiciones | -0,51 % (n=310, acierta 48,4 %, p=0,8372) | -1,11 % (n=308, acierta 49,7 %, p=0,9111) | -0,30 % (n=306, acierta 51,3 %, p=0,5824) | +0,01 % (n=137, acierta 47,4 %, p=0,5015) |
| Entrada: precio en la EMA 55 / parte baja | -0,04 % (n=409, acierta 50,1 %, p=0,5355) | +0,45 % (n=407, acierta 52,6 %, p=0,2378) | -0,13 % (n=406, acierta 51,2 %, p=0,5475) | +0,10 % (n=167, acierta 47,3 %, p=0,4186) |
| Entrada: Squeeze en valle rojo girando | -0,28 % (n=293, acierta 48,5 %, p=0,7203) | -1,13 % (n=292, acierta 49,0 %, p=0,9291) | -0,95 % (n=290, acierta 49,7 %, p=0,8242) | -0,06 % (n=129, acierta 48,1 %, p=0,5564) |
| Entrada: ADX con pendiente negativa | -0,61 % (n=427, acierta 49,6 %, p=0,9491) | -0,84 % (n=425, acierta 50,8 %, p=0,961) ❌ | -0,23 % (n=423, acierta 49,2 %, p=0,6294) | -1,17 % (n=171, acierta 48,0 %, p=0,987) ❌ |
| Entrada: cerca del POC aproximado | +0,09 % (n=319, acierta 53,0 %, p=0,4416) | -0,84 % (n=319, acierta 50,8 %, p=0,8462) | -0,90 % (n=318, acierta 50,0 %, p=0,7453) | -0,84 % (n=128, acierta 45,3 %, p=0,8611) |
| Zona no operable: mitad del lateral (comprando) | -0,54 % (n=279, acierta 48,4 %, p=0,8392) | -1,38 % (n=278, acierta 49,6 %, p=0,9461) | -0,87 % (n=277, acierta 52,3 %, p=0,7283) | +0,01 % (n=131, acierta 52,7 %, p=0,4875) |
| Zona no operable: topado / sobreextendido (comprando) | +1,01 % (n=243, acierta 49,8 %, p=0,0509) | +1,58 % (n=243, acierta 52,7 %, p=0,0509) | +2,93 % (n=243, acierta 53,9 %, p=0,045) ✅ | +0,42 % (n=98, acierta 50,0 %, p=0,3197) |
| Zona no operable: caída con ADX subiendo (comprando) | -0,52 % (n=405, acierta 52,6 %, p=0,9051) | -1,12 % (n=405, acierta 53,3 %, p=0,978) ❌ | -1,16 % (n=401, acierta 51,6 %, p=0,9071) | -0,36 % (n=166, acierta 54,8 %, p=0,7083) |
| Salida: ≥2 de 3 condiciones | -0,25 % (n=56, acierta 51,8 %, p=0,5834) | -0,99 % (n=56, acierta 50,0 %, p=0,6893) | -2,78 % (n=56, acierta 66,1 %, p=0,7952) | +1,86 % (n=28, acierta 53,6 %, p=0,1918) |
| Salida: parte alta del rango | -0,75 % (n=233, acierta 45,5 %, p=0,8981) | -1,87 % (n=233, acierta 44,6 %, p=0,956) ❌ | -4,30 % (n=233, acierta 42,1 %, p=0,983) ❌ | +0,14 % (n=96, acierta 53,1 %, p=0,4635) |
| Salida: divergencia bajista en Squeeze | -0,43 % (n=37, acierta 45,9 %, p=0,6304) | -1,50 % (n=37, acierta 35,1 %, p=0,7642) | +0,07 % (n=37, acierta 59,5 %, p=0,5035) | -1,54 % (n=18, acierta 38,9 %, p=0,7662) |
| Salida: pérdida de volatilidad tras impulso | +1,28 % (n=111, acierta 54,1 %, p=0,0799) | +1,58 % (n=109, acierta 53,2 %, p=0,1419) | +1,89 % (n=106, acierta 53,8 %, p=0,2627) | +1,59 % (n=63, acierta 57,1 %, p=0,1618) |
| Nota de la temporalidad ≥ 7,5 (score ≥ 0,5) | -0,18 % (n=223, acierta 49,3 %, p=0,6024) | +0,18 % (n=223, acierta 49,8 %, p=0,3976) | +1,51 % (n=223, acierta 52,5 %, p=0,1678) | -0,45 % (n=104, acierta 46,2 %, p=0,6973) |
| Nota de la temporalidad ≤ 2,5 (score ≤ −0,5) | +0,37 % (n=159, acierta 44,7 %, p=0,2987) | +0,36 % (n=158, acierta 46,2 %, p=0,3806) | +0,55 % (n=158, acierta 41,8 %, p=0,3546) | +0,22 % (n=55, acierta 49,1 %, p=0,4406) |

## Temporalidad 1s

Velas evaluadas — BTCUSDT: 353, ETHUSDT: 353

| Señal | a 5 velas | a 10 velas | a 20 velas | fuera de muestra (horizonte medio) |
|---|---|---|---|---|
| Tendencia «sana» (se espera que siga) | +7,90 % (n=18, acierta 38,9 %, p=0,1349) | +0,03 % (n=18, acierta 38,9 %, p=0,5135) | -4,47 % (n=18, acierta 44,4 %, p=0,5664) | n=4 |
| Tendencia «agotándose» (≥2 de 4 señales) | +10,30 % (n=6, acierta 83,3 %, p=0,1638) | +15,13 % (n=6, acierta 83,3 %, p=0,1718) | +25,44 % (n=6, acierta 83,3 %, p=0,1728) | n=3 |
| Agotamiento con ≥3 de 4 señales | n=0 | n=0 | n=0 | n=0 |
| Al menos 1 señal de agotamiento | +2,61 % (n=12, acierta 66,7 %, p=0,3656) | +2,16 % (n=12, acierta 50,0 %, p=0,4496) | +1,38 % (n=12, acierta 58,3 %, p=0,4875) | n=3 |
| Agotamiento: divergencia | n=3 | n=3 | n=3 | n=1 |
| Agotamiento: doble techo/suelo | n=3 | n=3 | n=3 | n=1 |
| Agotamiento: medias 10/55 juntándose | n=4 | n=4 | n=4 | n=0 |
| Agotamiento: ADX cede | +4,15 % (n=9, acierta 66,7 %, p=0,3177) | +9,80 % (n=9, acierta 55,6 %, p=0,2717) | +25,76 % (n=9, acierta 77,8 %, p=0,1988) | n=4 |
| Divergencia (RSI o Squeeze) | +2,73 % (n=12, acierta 50,0 %, p=0,3676) | +0,17 % (n=12, acierta 41,7 %, p=0,5105) | -36,06 % (n=10, acierta 40,0 %, p=0,9091) | +21,81 % (n=5, acierta 60,0 %, p=0,0599) |
| Divergencia solo en RSI | +7,15 % (n=5, acierta 80,0 %, p=0,2917) | +4,76 % (n=5, acierta 60,0 %, p=0,4096) | -26,87 % (n=5, acierta 60,0 %, p=0,7373) | n=2 |
| Divergencia solo en Squeeze | -1,75 % (n=7, acierta 42,9 %, p=0,5784) | +4,14 % (n=7, acierta 42,9 %, p=0,3576) | -5,29 % (n=6, acierta 50,0 %, p=0,5465) | n=3 |
| Divergencia en RSI y Squeeze a la vez | n=3 | n=3 | n=2 | n=2 |
| Divergencia + ADX con pendiente negativa (aviso reforzado) | +4,12 % (n=21, acierta 52,4 %, p=0,2458) | +1,62 % (n=21, acierta 57,1 %, p=0,4496) | +1,80 % (n=19, acierta 68,4 %, p=0,4296) | +7,60 % (n=8, acierta 62,5 %, p=0,1868) |
| Divergencia con ADX subiendo | -0,15 % (n=20, acierta 50,0 %, p=0,4905) | +2,48 % (n=18, acierta 61,1 %, p=0,3876) | +2,46 % (n=16, acierta 75,0 %, p=0,4086) | +22,11 % (n=6, acierta 100,0 %, p=0,011) ✅ |
| Ruptura de lateral confirmada | +0,76 % (n=5, acierta 80,0 %, p=0,4505) | -9,82 % (n=5, acierta 60,0 %, p=0,6683) | -4,22 % (n=5, acierta 60,0 %, p=0,5075) | n=2 |
| Posible ruptura (sin confirmar) | +5,03 % (n=23, acierta 52,2 %, p=0,1818) | -4,30 % (n=22, acierta 59,1 %, p=0,6823) | +1,38 % (n=22, acierta 63,6 %, p=0,4775) | +1,30 % (n=8, acierta 50,0 %, p=0,3876) |
| Entrada long: 4 de 4 condiciones | -8,52 % (n=8, acierta 62,5 %, p=0,7682) | +0,93 % (n=8, acierta 62,5 %, p=0,4326) | +16,13 % (n=7, acierta 85,7 %, p=0,3167) | +8,33 % (n=5, acierta 40,0 %, p=0,3217) |
| Entrada long 4/4 y ninguna zona no operable | -8,63 % (n=5, acierta 60,0 %, p=0,6883) | +8,57 % (n=5, acierta 60,0 %, p=0,3257) | n=4 | n=4 |
| Entrada long: ≥3 de 4 condiciones | +2,87 % (n=42, acierta 76,2 %, p=0,2388) | -1,43 % (n=42, acierta 57,1 %, p=0,5804) | +9,66 % (n=40, acierta 72,5 %, p=0,2777) | -3,54 % (n=15, acierta 40,0 %, p=0,6713) |
| Entrada: precio en la EMA 55 / parte baja | -5,27 % (n=50, acierta 52,0 %, p=0,9351) | -6,26 % (n=50, acierta 58,0 %, p=0,8332) | -8,36 % (n=48, acierta 56,2 %, p=0,6803) | -4,02 % (n=27, acierta 44,4 %, p=0,7203) |
| Entrada: Squeeze en valle rojo girando | +1,49 % (n=28, acierta 75,0 %, p=0,3836) | -1,35 % (n=28, acierta 67,9 %, p=0,5894) | +0,05 % (n=25, acierta 68,0 %, p=0,4905) | +5,29 % (n=14, acierta 64,3 %, p=0,2967) |
| Entrada: ADX con pendiente negativa | -1,67 % (n=44, acierta 56,8 %, p=0,6763) | -7,93 % (n=44, acierta 50,0 %, p=0,953) ❌ | -15,92 % (n=42, acierta 52,4 %, p=0,956) ❌ | -6,94 % (n=16, acierta 37,5 %, p=0,9471) |
| Entrada: cerca del POC aproximado | +4,73 % (n=35, acierta 77,1 %, p=0,1648) | +9,17 % (n=35, acierta 65,7 %, p=0,1349) | +26,53 % (n=33, acierta 81,8 %, p=0,0939) | +15,27 % (n=12, acierta 50,0 %, p=0,0789) |
| Zona no operable: mitad del lateral (comprando) | -9,91 % (n=26, acierta 38,5 %, p=0,994) ❌ | -13,24 % (n=25, acierta 40,0 %, p=0,974) ❌ | -35,67 % (n=25, acierta 40,0 %, p=1,0) ❌ | +2,53 % (n=8, acierta 37,5 %, p=0,4266) |
| Zona no operable: topado / sobreextendido (comprando) | -1,57 % (n=29, acierta 48,3 %, p=0,6334) | -3,60 % (n=29, acierta 58,6 %, p=0,6484) | -7,52 % (n=29, acierta 51,7 %, p=0,6513) | -14,46 % (n=14, acierta 35,7 %, p=0,961) ❌ |
| Zona no operable: caída con ADX subiendo (comprando) | -0,65 % (n=39, acierta 56,4 %, p=0,5874) | -4,59 % (n=39, acierta 48,7 %, p=0,7642) | -2,69 % (n=37, acierta 54,1 %, p=0,5904) | -9,45 % (n=16, acierta 25,0 %, p=0,9331) |
| Salida: ≥2 de 3 condiciones | +4,44 % (n=6, acierta 50,0 %, p=0,3616) | +16,14 % (n=6, acierta 66,7 %, p=0,1479) | +34,99 % (n=6, acierta 83,3 %, p=0,0989) | n=2 |
| Salida: parte alta del rango | -3,21 % (n=38, acierta 39,5 %, p=0,7562) | -1,09 % (n=38, acierta 39,5 %, p=0,5674) | +0,66 % (n=38, acierta 47,4 %, p=0,4945) | +6,52 % (n=16, acierta 56,2 %, p=0,2188) |
| Salida: divergencia bajista en Squeeze | +9,80 % (n=5, acierta 40,0 %, p=0,1808) | +7,80 % (n=5, acierta 40,0 %, p=0,3157) | +16,02 % (n=5, acierta 60,0 %, p=0,3506) | n=3 |
| Salida: pérdida de volatilidad tras impulso | -4,78 % (n=5, acierta 40,0 %, p=0,7173) | +13,86 % (n=5, acierta 60,0 %, p=0,2667) | +42,24 % (n=5, acierta 80,0 %, p=0,1518) | n=0 |
| Nota de la temporalidad ≥ 7,5 (score ≥ 0,5) | +1,02 % (n=36, acierta 52,8 %, p=0,3946) | +3,27 % (n=35, acierta 62,9 %, p=0,3347) | +7,68 % (n=35, acierta 54,3 %, p=0,3277) | -10,43 % (n=10, acierta 40,0 %, p=0,8921) |
| Nota de la temporalidad ≤ 2,5 (score ≤ −0,5) | +7,13 % (n=8, acierta 50,0 %, p=0,2368) | +0,97 % (n=8, acierta 62,5 %, p=0,5395) | +4,01 % (n=8, acierta 62,5 %, p=0,5355) | n=2 |

## Señal fuerte global (4 temporalidades juntas, medida en velas de 4h)

| Señal | a 6 velas de 4h | a 18 velas de 4h | a 42 velas de 4h | fuera de muestra (horizonte medio) |
|---|---|---|---|---|
| Señal fuerte global (la que avisa por Telegram) | +0,52 % (n=675, acierta 51,0 %, p=0,009) ✅ | +0,64 % (n=675, acierta 50,2 %, p=0,0679) | +1,30 % (n=675, acierta 51,7 %, p=0,0719) | +0,32 % (n=339, acierta 49,0 %, p=0,1858) |
| Señal fuerte ALCISTA | +0,42 % (n=531, acierta 51,8 %, p=0,024) ✅ | +0,32 % (n=531, acierta 51,2 %, p=0,2278) | +1,01 % (n=531, acierta 52,4 %, p=0,1289) | +0,40 % (n=269, acierta 51,7 %, p=0,1309) |
| Señal fuerte BAJISTA | +0,87 % (n=144, acierta 47,9 %, p=0,014) ✅ | +1,78 % (n=144, acierta 46,5 %, p=0,027) ✅ | +2,59 % (n=144, acierta 49,3 %, p=0,0799) | -0,03 % (n=70, acierta 38,6 %, p=0,5195) |
| Nota global ≥ 6 (score ≥ 0,2) | -0,02 % (n=666, acierta 48,5 %, p=0,5385) | +0,02 % (n=666, acierta 48,3 %, p=0,4775) | -0,48 % (n=664, acierta 48,8 %, p=0,7512) | +0,01 % (n=378, acierta 46,3 %, p=0,4845) |
| Nota global ≤ 4 (score ≤ −0,2) | +0,13 % (n=527, acierta 48,4 %, p=0,2488) | -0,36 % (n=526, acierta 45,6 %, p=0,8042) | -0,33 % (n=524, acierta 43,1 %, p=0,6513) | -0,33 % (n=299, acierta 45,2 %, p=0,7872) |

---
Medir el pasado no garantiza el futuro. Con tantas señales y horizontes, alguna saldrá «significativa» por pura casualidad: fíate solo de lo que se repite en las dos monedas y fuera de muestra.