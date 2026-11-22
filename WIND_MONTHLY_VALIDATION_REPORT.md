# Měsíční validace větrných kandidátů

Zpracováno 81 individuálních kandidátů ve 33 obdobích; vytvořeno 162 párování období–stanice. Snapshot `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`.

Srovnání používá přesné UTC časy, pouze CHMI quality 0 a bez interpolace. Loučka rychlosti jsou převedeny z km/h na m/s. Výsledky jsou regionální kontext, ne fyzická validace ani kalibrace.

| Veličina | Kandidáti | Měsíc–stanice | UTC páry | Spárováno / kvalitní reference (min.) | Kvalitní reference / očekávané sloty (min.) | Bias reference−Loučka | MAE | RMSE | Korelace |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Wind speed: Loučka archive windSpeed vs CHMI Fprum | 31 | 62 | 268,356 | 99.12% | 67.11% | -1.153 m/s | 1.404 m/s | 1.785 m/s | 0.507 |
| Wind gust: Loučka archive windGust vs CHMI Fmax | 31 | 62 | 268,285 | 99.12% | 67.11% | -0.707 m/s | 1.640 m/s | 2.126 m/s | 0.700 |
| Wind direction: Loučka archive windDir vs CHMI Dprum | 19 | 38 | 164,831 | 98.97% | 85.44% | circular -76.2° mean | 57.6° circular | — | — |

## Význam a omezení

- ČHMÚ popisuje 10minutové prvky D, F, Dprum, Fprum, Dmax, Fmax a Casmax; rozlišení prvků je zachováno v surových záznamech.
- Fprum je 10minutová průměrná rychlost větru; Fmax je prvek maximální rychlosti. Přesné okno lokálního `windGust` ani shoda jeho časové podpory s ČHMÚ Fmax nejsou doloženy.
- Dprum je směrový průměr. Směr se vyhodnocuje kruhově (cirkulární průměr, koncentrace a nejkratší úhlový rozdíl), nikoli aritmetickým průměrem přes hranici 0°/360°.
- Stejný časový štítek neprokazuje stejnou délku intervalu, expoziční podmínky, stanoviště ani snímač. Souřadnice a expozice loučského anemometru nejsou ověřeny.
- Vysoká korelace ani nízký rozdíl samy neodstraňují blokaci provenience nebo fyzické validace. Žádná korekce ani publikační povolení se nevytváří.

Všechny detailní řádky, quality counts, hashované soubory, denní a šestihodinové struktury a kruhové statistiky jsou v `MONTHLY_WIND_REFERENCE_VALIDATION.json`.

### Zdrojové hashy

- `data/chmi-2018/raw/10m-0-203-0-11777-201801.json`: `c42a3637921d5794c50098c9dc4570917c836fe3866e905af49e7528ed158c40`
- `data/chmi-2018/raw/10m-0-203-0-11777-201802.json`: `f43ec7557c9f4e160f94d9a04024b5d45fd4235edc729d66aa0efe4299561844`
- `data/chmi-2018/raw/10m-0-203-0-11777-201803.json`: `5822fa65978aab0a81a9e7e3b94e2f7d79c78c382590f2c8c776ae482e217439`
- `data/chmi-2018/raw/10m-0-203-0-11777-201804.json`: `49e874e9c8597c55f873b6591585db0fec4e083af4d5b877127f0496d58b3932`
- `data/chmi-2018/raw/10m-0-203-0-11777-201805.json`: `b33573bb30f81e598390169c00e84aeb229892797317056246f994ce657747bf`
- `data/chmi-2018/raw/10m-0-203-0-11777-201806.json`: `87cdcbdb35aec721b3c1f29307b0e6633a5730eebb9fc8bfd44e558f0ef8a55f`
- `data/chmi-2018/raw/10m-0-203-0-11777-201807.json`: `f4b960d8233928dcd0adf9a4de6b6a9e7c3d301dff2b303e94430db850b38a9d`
- `data/chmi-2018/raw/10m-0-203-0-11777-201808.json`: `6987df2e47d129351f90b82ce981f6601bc8d90398d171603af6d9281bcdfe44`
- `data/chmi-2018/raw/10m-0-203-0-11777-201809.json`: `76b432c288648f84b93980e4d1a5be8c747d59c7a9fb489c9e235f028f90c0fb`
- `data/chmi-2018/raw/10m-0-203-0-11777-201810.json`: `e1a9fe8f314721901f3c5fabc1fe63cc9587c73ea161664f0e06d294e8656015`
- `data/chmi-2018/raw/10m-0-203-0-11777-201811.json`: `8219ac22ecc0998d5442a3f2099479b3650e10cd3fc9cadf8b5fa28fbfedb4c3`
- `data/chmi-2018/raw/10m-0-203-0-11777-201812.json`: `f28d4fe8a7195d8a700c4ff9d085d3b04d1552569b849069479fddc0520a41fb`
- `data/chmi-2018/raw/10m-0-203-0-11778-201801.json`: `effc6dabc6279a9f9488b734e16edd023fd76dadb0482492b91365b6d44831b0`
- `data/chmi-2018/raw/10m-0-203-0-11778-201802.json`: `d9aeefec79b3c19f4cd8d325675635ec5c7f17962e67f0ed23abb1d07034fbb1`
- `data/chmi-2018/raw/10m-0-203-0-11778-201803.json`: `68bcd3fdbb68a167aa20d148d16824dd84fd6db7bf63c861faf49286c17ba407`
- `data/chmi-2018/raw/10m-0-203-0-11778-201804.json`: `23406f7c830074ea7f03cadd904abca34c051e5a5206ca4f46d9d48a21bbb11a`
- `data/chmi-2018/raw/10m-0-203-0-11778-201805.json`: `48d61601d6b5aa0c6bca62efbf60144977c16178532ac0734e2c6149a9c88a0d`
- `data/chmi-2018/raw/10m-0-203-0-11778-201806.json`: `100de939aa350988283a579bbf480a0f75f2128b17aa04d08172c015864ca4d1`
- `data/chmi-2018/raw/10m-0-203-0-11778-201807.json`: `0a4ba4246d27883441912fbb1caba54225b65e0b2db9763bb29a8e2c07e93a39`
- `data/chmi-2018/raw/10m-0-203-0-11778-201808.json`: `0fa821aedfc37e9c8bf0e1f2e3b46603548081cc17e8dadc6ab2ea9dae775ba4`
- `data/chmi-2018/raw/10m-0-203-0-11778-201809.json`: `2cc2bb9ca2611d17ed408aa1ab7a47111b32ef761555745ed2021a5127406d71`
- `data/chmi-2018/raw/10m-0-203-0-11778-201810.json`: `3291f97f9777a619da1ad6df833d7622bd37753a3bf49e9610ec56c30ae757ef`
- `data/chmi-2018/raw/10m-0-203-0-11778-201811.json`: `8eecb94664353073dc3a205c0c108cda44fb67e2c0b3ae32482e68fcaea1314d`
- `data/chmi-2018/raw/10m-0-203-0-11778-201812.json`: `e12edf62fcac184e1cc0fa60c2b596782aa3b01c871f32aa3c37fb1a1e3a09ea`
- `data/chmi-2026-recent/raw/10m-0-203-0-11777-202601.json`: `b7e01c6ed701081e981b85a935556316585d53ebae5ffa020ccf19a13325684a`
- `data/chmi-2026-recent/raw/10m-0-203-0-11777-202602.json`: `d1ec9c25cbbb3cb8a68f596b8aee4602e741241e2cd086d4614f1c4e2be54a22`
- `data/chmi-2026-recent/raw/10m-0-203-0-11778-202601.json`: `80d95f0279f04d77e8f2a1d20981b32eae9e9c5a77e0b76c021dc4c4758dbf37`
- `data/chmi-2026-recent/raw/10m-0-203-0-11778-202602.json`: `ad24ed6b72e9c6dfe74813a1a2e286e9eb407bbcc6402dfc3c24fc80927183cb`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201804.json`: `49e874e9c8597c55f873b6591585db0fec4e083af4d5b877127f0496d58b3932`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201805.json`: `b33573bb30f81e598390169c00e84aeb229892797317056246f994ce657747bf`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201806.json`: `87cdcbdb35aec721b3c1f29307b0e6633a5730eebb9fc8bfd44e558f0ef8a55f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201807.json`: `f4b960d8233928dcd0adf9a4de6b6a9e7c3d301dff2b303e94430db850b38a9d`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201808.json`: `6987df2e47d129351f90b82ce981f6601bc8d90398d171603af6d9281bcdfe44`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201809.json`: `76b432c288648f84b93980e4d1a5be8c747d59c7a9fb489c9e235f028f90c0fb`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201810.json`: `e1a9fe8f314721901f3c5fabc1fe63cc9587c73ea161664f0e06d294e8656015`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201811.json`: `8219ac22ecc0998d5442a3f2099479b3650e10cd3fc9cadf8b5fa28fbfedb4c3`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201812.json`: `f28d4fe8a7195d8a700c4ff9d085d3b04d1552569b849069479fddc0520a41fb`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201901.json`: `0c46eb2347191a8584788040a3fe31e81480958c39d4d58aeb7aa58b4efc247f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201902.json`: `4c15132109297e4ee65ef3c79638151cfd7d967b4c309fef29fd542ebf427bed`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-201903.json`: `fe3e11051fb4537e4c547246cc2c5763e9789d55d4d7ddad3b48bc13952d58c4`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202012.json`: `ec168cf3d4f017c95319157509d1ec12a7f59faefc6c564aa624acaffe0748b8`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202202.json`: `b1637163326728666101da0f2cf44cd30dfc1990b582c3e36638e5a041e04aaa`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202204.json`: `7fb486d6aad40a551eed10ee7a2cccd493824ea52e754abc9b76028cead2ac7c`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202205.json`: `b336ddfc29b1c43397a202172842c95e4c5e06af0019b40e8541724c1b89cbaa`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202206.json`: `3e266c6069046ccc89bd99fa2b0bd41b7f254d34d5c59ee8f512daff5dc2ac55`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202207.json`: `00151a0ac17a81ebf7e9c9ece8feee6cbdc910f4023887d347ce76438f931af6`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202211.json`: `98029a5adac544b87a1996e99da2bfc12e394140d66c6937605a27e0452524f2`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202212.json`: `44daec3cd6bfb95d4e429cef23a37ca1b6ccc7e9f517c2d06f6548ad4485d4c9`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202301.json`: `d7be93fa541882ecca0639c91f2c0324ea2efede9ec6eda363958262ec5b4608`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202302.json`: `8271c69a2591ff83eda44f3270bc2f247795d9c1022f3649c9a040031f20d156`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202303.json`: `dce052207ea076a0832ea9173d08ca9576370478bf3cd8d96d33a8554dcffe29`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202304.json`: `0488d9429154d0a45aae2f639b0f07507f4d85ab3f449a53cb186be139088e6a`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202306.json`: `3e1993752bad03a2a9c282c45519ed11865d2c136be92d3c02435a10a8dd6ed1`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202307.json`: `4950b16ea99249e9d8f47629c7850724509e9682c7a73f01a0537f4f8fedfd47`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202308.json`: `ae4e0f81e511dcdcedc4e018eb80e698e1c1f057848ae7902a2647df07f4fd86`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202309.json`: `9b5d5a9f03694c115f2ae05454f234c0c441856d85eeb955b7e497bbb7c57c4a`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202310.json`: `0119da902881e40841915750bb5209ae6b388047fc3808ae0f8912466dab2f80`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202312.json`: `20d4415c2b43dd1b10174ffc983369d25b5e8d69fe5238f45b15e0a269b457a1`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202402.json`: `ccff711bcf4effcf2ebf4d3a31a1f45e7bcfe85145a693826c313a39a4e78972`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202403.json`: `e34f25859df014e122b432a9ad2f325bae24addab91422eab315c276290e447c`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202404.json`: `8bf0ef4bcb2812ff3e6e2c9c81860d56567b7a523299587ec47dbe7a99ab4653`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202405.json`: `df4616ecbfc1ac9f028ba17ff670aeb893c39aae5e16e5b9a6c68d001429840f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202406.json`: `833ee41b4a3730d11226eb0499a9ba76cf736f3db046400399a409d6771decf9`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202407.json`: `ee37af0fbd83a19f2469e0a1a91d3711d3f7c99701525518a652275cd05a4d5f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202408.json`: `92c6c7e3fbbcf7e3b24362540e6857971b04b40a599eae31a3fcc0c93a63ed57`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202410.json`: `203d4bc795daa8308edc4c32b3a82117b5ed275cccfecf7ef30f4ac58d0dceb8`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202411.json`: `9cedefb8e90dfac8bb4133354a28068f3fd809b25f69f52fede0f9be4aa9098f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202412.json`: `5c0a8bba88ea7e8b1b45081f254ec0c73ab5b8f77523c39e74034e0a12063163`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202504.json`: `ff27b6b0600042996fca4e97de27c010729630ae9687bf83bbfd746bf520e9e1`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202505.json`: `06a708334e90a5ff5682cda6e32e7d6426dad6f803892cfb5e5f75aacca47d5e`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202506.json`: `79d2c9d1dd7be62da1b926b328a8dee3134d4cde729fff9c7e1429a071d95410`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202507.json`: `129c2ecbcc042233be8a756c0b4c442347fbbe5d2fc88afd121571bae4c4b200`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202509.json`: `8acd554ac10f24c26300b912e51111994838939d5783827868e5623664bb5bf2`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11777-202510.json`: `a4af4b75f784d3d592f5ed6ab187c0227c7290a9fd0610cd9a39dd045b3d4a1a`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201804.json`: `23406f7c830074ea7f03cadd904abca34c051e5a5206ca4f46d9d48a21bbb11a`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201805.json`: `48d61601d6b5aa0c6bca62efbf60144977c16178532ac0734e2c6149a9c88a0d`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201806.json`: `100de939aa350988283a579bbf480a0f75f2128b17aa04d08172c015864ca4d1`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201807.json`: `0a4ba4246d27883441912fbb1caba54225b65e0b2db9763bb29a8e2c07e93a39`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201808.json`: `0fa821aedfc37e9c8bf0e1f2e3b46603548081cc17e8dadc6ab2ea9dae775ba4`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201809.json`: `2cc2bb9ca2611d17ed408aa1ab7a47111b32ef761555745ed2021a5127406d71`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201810.json`: `3291f97f9777a619da1ad6df833d7622bd37753a3bf49e9610ec56c30ae757ef`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201811.json`: `8eecb94664353073dc3a205c0c108cda44fb67e2c0b3ae32482e68fcaea1314d`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201812.json`: `e12edf62fcac184e1cc0fa60c2b596782aa3b01c871f32aa3c37fb1a1e3a09ea`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201901.json`: `95f5ea50d8e5b40f62a343f174a23c9671cee5e03bfb29b4ead3d6b08208e2c0`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201902.json`: `d8864edade71bab22c24342e67d9b66cbf4b5c1d4bffe2b05b13b334b966ddf6`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-201903.json`: `2eb04e4e9b25380a10d5cda2e9604c683b64e58977cfcdcc019a45cc0c767e06`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202012.json`: `f41832d1e1a66e8606347eb163d8eb879aa0b5eeaf90a4ab4cb50803ccec8d52`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202202.json`: `e5c62d082558732d465ef41195991e7aee05896d795f67f2678ceb67081eab06`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202204.json`: `d4da94331ad436048b9af235f130c9462abfff86470d2268a4b7312287223ced`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202205.json`: `5ec1c017735abb27f05e64f342f0bbb80ffda3657258fc3772bea2bd6aaea0e1`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202206.json`: `d28a207599715228076b7e2dd58203b60a281b7fec1d9008fe5fa2230bb50fef`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202207.json`: `023c674ebf5e928bda482d9a2ce5b2bf42bdf63d1cb870f426a1fbc1f4572fcd`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202211.json`: `9ff0dd593a6da89c6b54afa3a0f7a96218ed739050e00a34f52b7e08306f5c77`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202212.json`: `120029221a6f8f034415ec4ea0906bd3237dd8ce8cc48f21789bce9bedbe1a84`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202301.json`: `62b55ee3fa3c2b4f6ec49e5451d8a6a26e40d31233a34a9fbc459cbca7840b06`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202302.json`: `0d5fcb80ea7cc6289c239ed3927eb6b6b8ca15b3d988b95843e7d2a50915f4d7`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202303.json`: `7dcbbe80a67faa9d8e252cc97c76dcd98457b9ce6d05641f057c3d88fb7658bc`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202304.json`: `1a0fbbb314c89bf5cb528d7262db522121aad00e6c9ac73fc35318bdfdb7b473`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202306.json`: `bafc60cd82d837701437864b65bdeb419a20b2f5d3443c0a253d9471616c834e`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202307.json`: `7947c3f1f3a6efd8dbcfd4f54e39efc5763cb72f631207c8e8d49de0cd3ca61d`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202308.json`: `4a018f1e006fe80ba234fe1fefd4c2c3cdc11ea82929e7f7f07154902c1479d2`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202309.json`: `efb394dbececf4891e6ae010cc431e532c72669fcfb335da4fcd00d796593334`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202310.json`: `298983fa538f4dbc5a4971fe984d9c538010a853eba12bfe1e92efb44640ef62`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202312.json`: `34cb7c759a97842edb3bef69e01fe33ef84508c53a1373badd544fd4175f849d`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202402.json`: `830160235c00f525823cf8b1b8edfbca45c8575ab4e45ac543226b17d7def18f`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202403.json`: `bfe9a792b876918db8ce4cd5005cc20a4046846c06a91fb92041dcb057ba3b90`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202404.json`: `a2ba6cf29dbfeebfe929c751573ad6333973c7a7fb249a7fd37870165ec09810`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202405.json`: `06b785a2f09b9a6d5bb1ad4e86286b88c0f11bf6b5f5003a5cce7a391d5f6561`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202406.json`: `8d8cdead38613e54f1a55c77dfa39cce4d790eb3f7b0a1289956bcb6872d9d4e`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202407.json`: `36890a6fa8ae94fb10f02688db332194c67c78b42cca2c072bb4a71987723439`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202408.json`: `1ffdc75cda746f954d168d70f1215d58611d7db27e22ac75acefe119bfee1619`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202410.json`: `89b4c737ca23682ba60ea2f27fe749079893277353cc2b4ab16b067e2b052d2c`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202411.json`: `3eaf83d3e9b5576350f6e3ecb4fc77202d1b9dad1e96b29f10643391e051d585`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202412.json`: `2bbb06c115b3536d0ea46b30fe0373125d68a9872b9d5d75b660b6c20776a68c`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202504.json`: `741b1f59bb7c3825a07f54f030134b37c312f81e5368d7635b1a07f1a77a6550`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202505.json`: `0050d60d9c61aa3f8b4b77fbecd9ff5276404fef82c272c7a26e2a54cb81479e`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202506.json`: `c632366bdf30a9409283f27b5921531508e4c889a8ad3539e67e7bf882b6b467`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202507.json`: `c1cb1dc7540739f11674b24415a3ec0b7b53d271b666f5d94cf4412b9a0ce576`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202509.json`: `704c872a37b4d8bc2f13910b0a82ef885ec56659746099c45f9f904a6e23036a`
- `data/chmi-priority-temperature/raw/10m-0-203-0-11778-202510.json`: `bc8c57babbbc8c4e180dd67974c098973a8bca27abe27e98cc531c1bf93e9530`
