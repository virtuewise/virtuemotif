import time
import torchaudio


def main() -> None:
    t0 = time.time()
    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model(with_star=True)
    n = sum(p.numel() for p in model.parameters())
    print(f"ok params={n/1e6:.1f}M seconds={time.time()-t0:.1f}", flush=True)


if __name__ == "__main__":
    main()
