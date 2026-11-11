# Backtest de las señales — resultados (11/11/2026)

**Qué se ha medido.** Histórico de Binance de BTC y ETH desde agosto de 2017 hasta hoy (unas 20.000 velas de 4h, 3.400 diarias y 480 semanales por moneda). En cada vela cerrada el motor recibe solo lo que habría visto en directo y se apunta qué señales daba. Después se mira cuánto se movió el precio 5, 10 y 20 velas más tarde.

**Con qué se compara.** Con el azar: las mismas señales, con el mismo sentido, colocadas en momentos aleatorios. La «ventaja» es la diferencia. Así una señal de compra no parece buena solo porque BTC ha subido en general.

**Fuera de muestra.** El último 40 % del histórico (desde marzo de 2023) se mira aparte. Lo que solo funciona antes de 2023 no cuenta como fiable.

## Qué ha salido (velas de 4h, a 10 velas vista ≈ 40 horas)

| Señal | Veces | Ventaja | Acierta | ¿Se mantiene desde 2023? |
|---|---|---|---|---|
| Nota de la temporalidad ≥ 7,5 | 1.298 | +0,58 % | 53,6 % | Sí (+0,36 %) |
| Ruptura de lateral confirmada | 394 | +0,53 % | 51,3 % | No (−0,10 %) |
| Tendencia «sana» (que siga) | 1.033 | +0,52 % | 53,0 % | No (−0,04 %) |
| Señal fuerte global, a 3 días | 675 | +0,64 % | 50,2 % | A medias (+0,32 %, sin ser concluyente) |
| Nota de la temporalidad ≤ 2,5 | 1.242 | +0,05 % | 44,8 % |Tampoco |
| Divergencia (RSI o Squeeze) | 715 | −0,06 % | 52,9 % |Tampoco |
| Divergencia + ADX cayendo (aviso reforzado) | 1.064 | −0,12 % | 51,6 % |Tampoco |
| Patrón de entrada long 4 de 4 | 651 | −0,15 % | 50,7 % |Tampoco |
| Tendencia «agotándose» (≥2 de 4) | 506 | −0,59 % | 46,4 % | Neutro (+0,17 %) |
| Agotamiento: doble techo/suelo | 275 | −0,72 % | 46,2 % | Neutro |
| Zona no operable «cuchillo» (comprar ahí) | 2.546 | −0,27 % | 53,1 % | Sí (−0,32 %) |
| Zona no operable «topado» (comprar ahí) | 1.320 | +0,48 % | 52,3 % | No (+0,11 %) |

## Lectura

1. **Lo que tuvo ventaja fue seguir la tendencia.** Una nota alta en 4h es la única señal que aguanta en las dos monedas y también desde 2023. La señal fuerte global apunta en la misma dirección, pero con menos certeza.
2. **Los avisos de giro no han funcionado.** Divergencias, aviso reforzado y agotamiento no predicen la caída mejor que el azar. Entre 2017 y 2023 el aviso de agotamiento incluso fue al revés: el precio tendía a seguir. Desde 2023 es neutro.
3. **El patrón de entrada completo (4 de 4) no da ventaja medible**, tal como lo calcula el motor.
4. **La zona «cuchillo» sí se confirma:** comprar mientras el precio cae con el ADX subiendo sale peor que el azar, antes y después de 2023.
5. **La zona «topado» sale al revés que en la guía** hasta 2023 (comprar extendido siguió subiendo); desde 2023 es neutra.
6. **En diario y semanal no hay nada concluyente:** hay pocas señales (un centenar de avisos de agotamiento en diario, menos de 10 en semanal).

## Umbrales

Se probaron variantes de los umbrales de aviso (nº de señales de agotamiento, exigencias de la ruptura, umbral de la nota y de la señal fuerte), eligiendo en los datos hasta 2023 y juzgando en los de después. **Ninguna variante gana con claridad a los umbrales actuales fuera de muestra, así que no se propone cambiar ninguno.** Detalle en `umbrales.md` de la rama `backtest-data`.

## Límites

- Mide el cierre a N velas contra el azar. No es una simulación de operaciones con stop, toma de beneficios ni comisiones. Las ventajas son pequeñas (medio punto en 40 horas).
- BTC y ETH se mueven muy parecido: que algo salga en las dos no son dos confirmaciones independientes.
- Se evalúa cómo el motor detecta cada cosa. Una divergencia que tú ves a ojo en TradingView puede no coincidir con la que detecta el código.
- Solo se han variado los umbrales de aviso, no los parámetros internos de detección (ventanas de pivotes, ATR, etc.).
- Con tantas señales y horizontes, alguna sale «significativa» por casualidad. Por eso solo cuenta lo que se repite fuera de muestra.
- El pasado no garantiza el futuro. Esto no es una recomendación de inversión.

## Cómo repetirlo

GitHub → Actions → «Backtest de señales» → Run workflow (unos 20 minutos). Publica histórico, filas, `informe.md` y `umbrales.md` en la rama `backtest-data`.
