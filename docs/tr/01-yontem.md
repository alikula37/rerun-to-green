# Yöntem

`rerun-to-green` tek bir soruyu public veriyle yanıtlar:

> Bir CI koşusu başarısız olunca, aynı kod (aynı workflow, aynı commit) yeniden
> çalıştırıldığında — kod değişmeden — ne kadar sıklıkla yeşile dönüyor?

## Veri kaynağı

GitHub REST API, `List workflow runs for a repository`:

```
GET /repos/{owner}/{repo}/actions/runs?per_page=100
```

Sadece public metadata: `head_sha`, `conclusion`, `event`, `run_attempt`,
`created_at`, `run_started_at`, `updated_at`, `workflow_id`, `path`.

Kaynak kod yok, log yok, PR metni yok, kullanıcı verisi yok.

## Örneklem

GitHub Actions kullanan, dil ve boyut açısından çeşitli 32 seçili açık kaynak repo.
Tamamı public. 90 günlük pencere istenmiştir; o pencerede 6.000'den fazla koşusu olan
repolarda en yeni 6.000 koşu limiti uygulanmıştır.

| Grup | Repolar |
|---|---|
| Python | apache/airflow, pandas-dev/pandas, numpy/numpy, home-assistant/core, ansible/ansible, encode/django-rest-framework, psf/requests |
| TypeScript/JS | microsoft/playwright, sveltejs/svelte, vercel/next.js, microsoft/TypeScript, angular/angular, pnpm/pnpm, vuejs/core, vitejs/vite, webpack/webpack, eslint/eslint, n8n-io/n8n, jquery/jquery |
| Rust | rust-lang/rust, denoland/deno |
| Go | golang/go, kubernetes/kubernetes, grafana/grafana, hashicorp/terraform, prometheus/prometheus, etcd-io/etcd |
| Java/Kotlin | spring-projects/spring-boot |
| C/C++ | godotengine/godot, grpc/grpc |
| Ruby | rails/rails |
| ML (Python/C++) | pytorch/pytorch |

## Tanımlar

**Koşu (run)** — bir workflow yürütmesi (bir `workflow_runs` kaydı).

**Kırmızı** — sonuç `failure` veya `timed_out`.

**Yeşil** — sonuç `success`.

**Episode** — aynı `(repository, workflow_id, head_sha)` değerindeki tüm yürütmeler.
Aynı commit birden çok çalıştırılabildiği için (rerun, manuel dispatch, zamanlanmış
koşu) episode, tek kod durumunun "deneme dizisi" olarak doğal birimdir.

**Aynı commit'te yeniden çalıştırma** — birden çok yürütmesi olan episode
(`n_entries > 1` veya `run_attempt > 1`).

**İyileşen (entry bazlı)** — en az bir kırmızı yürütmesi olan ve son yürütmesi yeşil
biten episode.

## Neden iki recovery sayısı?

GitHub rerun'ları iki şekilde kaydediyor; bu yüzden iki sayı raporluyoruz:

1. **Entry bazlı (aynı commit recovery):** kırmızı bir run kaydından sonra aynı
   `head_sha` ile gelen yeşil bir run kaydı. Her aynı-commit iyileşmesini yakalar —
   "rerun butonuna basmadan" gerçekleşen zamanlanmış/workflow yeniden koşuları dahil.
2. **Attempt bazlı (rerun'a basma):** `run_attempt ≥ 2` olan koşular. GitHub API
   attempt'leri tek kayıtta toplar; bu yüzden rastgele örneklemle doğrulama yapıyoruz:
   örneklenen her koşu için attempt #1'i (`GET .../attempts/1`) çekip gerçekten
   başarısız olduğunu teyit ediyor, sonra nihai sonuca bakıyoruz.

## Yeşile dönme süresi

İyileşen episode'lar için: ilk kırmızı yürütmenin başlangıcından ilk yeşil yürütmenin
tamamlanmasına kadar geçen dakika. İyileşen episode'lar üzerinde medyan ve P90 olarak
raporlanır.

## Pipeline

```
src/fetch_runs.py          -> data/raw/*.json.gz   (ham run metadata)
src/analyze.py             -> data/processed/*     (episode'lar + özet)
src/validate_attempts.py   -> attempt bazlı recovery örneklem doğrulaması
```

## Notlar

- Kırmızı bitip *yeni* commit'te yeniden çalıştırılan episode'lar tanım gereği "aynı
  commit'te yeniden çalıştırma" değildir — onlar kod değişikliğiyle düzeltilmiştir.
- Aynı commit'te yeşile dönmek kodun doğru olduğunu kanıtlamaz; sadece o koşuda
  failure'ın commit'ten kaynaklanmadığını gösterir.
- Attempt bazlı sayı, geliştiricinin rerun yapmayı *seçtiği* koşullara bağlıdır —
  seçilmiş bir örneklemdir (geliştiriciler genelde flaky olduğunu düşündükleri
  koşuları yeniden çalıştırır).
