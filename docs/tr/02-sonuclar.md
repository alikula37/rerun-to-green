# Sonuçlar

2026-08-19'da 32 repodan 143.061 public GitHub Actions koşusu üzerinde ölçüldü
(90 güne kadar geçmiş; yoğun repolarda en yeni 6.000 koşu limiti).

## Başlık

| Soru | Cevap |
|---|---|
| Aynı commit'te yeniden çalıştırılan başarısız koşu | **~%18** (1.785 / 10.047) |
| Aynı commit'te yeniden çalıştırılan ve yeşile dönen (entry bazlı) | **~%28** (498 / 1.785) |
| Rerun'a basma durumu (attempt bazlı, örneklem) | **~%75** (63/83) |
| Yeşile dönme süresi medyan (iyileşenler) | **3,8 dk** |
| Yeşile dönme süresi P90 (iyileşenler) | **171 dk (~2,9 sa)** |

## İki recovery oranı ne demek

- **Entry bazlı (~%28):** run listesinde görülen her aynı-commit iyileşmesi —
  zamanlanmış yeniden koşular ve yeniden tetiklenen workflow'lar dahil, yalnızca
  insanın rerun'a basması değil.
- **Attempt bazlı (~%75):** GitHub'ın en az bir kez yeniden çalıştırıldığını kaydettiği
  (`run_attempt ≥ 2`) ve ilk denemesi gerçekten başarısız olan koşular
  (400 yeniden-çalıştırılan koşunun rastgele örneklemi — 83'ü gerçekten başarısız ilk
  denemeye sahipti, 63'ü yeşile döndü; `GET .../attempts/1` ile doğrulandı).

## Olay türüne göre recovery (entry bazlı)

| Tetikleyici | Kırmızı episode | Aynı commit rerun | İyileşen | Oran |
|---|---:|---:|---:|---:|
| Geliştirici tetikli (push, PR, dispatch) | 9.296 | 1.371 | 306 | %22,3 |
| Otomatik (schedule, workflow_run, ...) | 729 | 400 | 189 | %47,2 |
| Diğer | 22 | 14 | 3 | %21,4 |

Otomatik yeniden koşular daha çok iyileşiyor (gece/periyodik işler sonraki koşuda
düzeliyor) — beklendik: o koşular hiçbir kod değişikliğine bağlı değil.

## Repo bazında (entry bazlı)

| Repository | Kırmızı episode | Aynı commit rerun | İyileşen | Oran |
|---|---:|---:|---:|---:|
| microsoft/playwright | 1.200 | 229 | 145 | %63,3 |
| rust-lang/rust | 1.168 | 18 | 2 | %11,1 |
| godotengine/godot | 932 | 277 | 1 | %0,4 |
| denoland/deno | 894 | 113 | 20 | %17,7 |
| hashicorp/terraform | 554 | 153 | 67 | %43,8 |
| etcd-io/etcd | 494 | 37 | 6 | %16,2 |
| home-assistant/core | 461 | 18 | 5 | %27,8 |
| vitejs/vite | 458 | 91 | 13 | %14,3 |
| apache/airflow | 457 | 90 | 8 | %8,9 |
| prometheus/prometheus | 425 | 53 | 41 | %77,4 |
| pytorch/pytorch | 392 | 95 | 6 | %6,3 |
| pandas-dev/pandas | 343 | 8 | 1 | %12,5 |
| vuejs/core | 313 | 182 | 107 | %58,8 |
| grafana/grafana | 243 | 43 | 1 | %2,3 |
| spring-projects/spring-boot | 223 | 23 | 8 | %34,8 |
| vercel/next.js | 196 | 103 | 18 | %17,5 |
| pnpm/pnpm | 180 | 58 | 11 | %19,0 |
| rails/rails | 169 | 13 | 2 | %15,4 |
| angular/angular | 160 | 51 | 7 | %13,7 |
| eslint/eslint | 145 | 16 | 7 | %43,8 |
| webpack/webpack | 136 | 11 | 0 | %0,0 |
| sveltejs/svelte | 135 | 20 | 0 | %0,0 |
| numpy/numpy | 117 | 30 | 9 | %30,0 |
| n8n-io/n8n | 109 | 27 | 7 | %25,9 |
| grpc/grpc | 78 | 13 | 2 | %15,4 |
| encode/django-rest-framework | 23 | 1 | 0 | %0,0 |
| golang/go | 21 | 0 | 0 | — |
| microsoft/TypeScript | 18 | 11 | 4 | %36,4 |
| psf/requests | 2 | 1 | 0 | %0,0 |
| jquery/jquery | 1 | 0 | 0 | — |

> Repo arası geniş dağılım (%0–77) çok farklı CI kurulumlarını yansıtır: matrix
> build'ler, flaky-test yönetimi, approval-gated environment'lar. Başlık sayısı bu
> yüzden bir toplamdır — tek bir proje için vaat değildir.
