import { ChangeEvent, Dispatch, SetStateAction, useEffect, useMemo, useState } from "react";

type Platform = "windows" | "macos" | "ios" | "android" | "all";
type Frame = "rounded" | "circle" | "square";

const API_URL = "http://127.0.0.1:8000";

const platformLabels: Record<Platform, string> = {
  windows: "Windows",
  macos: "macOS",
  ios: "iPhone (iOS)",
  android: "Android",
  all: "Todo en un ZIP",
};

function App() {
  const [platform, setPlatform] = useState<Platform>("all");
  const [frame, setFrame] = useState<Frame>("rounded");
  const [zoom, setZoom] = useState<number>(1);
  const [moveX, setMoveX] = useState<number>(0);
  const [moveY, setMoveY] = useState<number>(0);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [status, setStatus] = useState<string>("Selecciona plataforma y sube una imagen");
  const [busy, setBusy] = useState<boolean>(false);
  const [previewBusy, setPreviewBusy] = useState<boolean>(false);

  const canProcess = useMemo(() => Boolean(imageFile), [imageFile]);

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] ?? null;
    setImageFile(next);
    setPreviewUrl("");
    setStatus(next ? "Imagen lista para previsualizar" : "Selecciona una imagen");
  };

  const buildFormData = () => {
    if (!imageFile) {
      throw new Error("No hay imagen seleccionada");
    }

    const formData = new FormData();
    formData.append("image", imageFile);
    formData.append("platform", platform);
    formData.append("frame", frame);
    formData.append("zoom", String(zoom));
    formData.append("move_x", String(moveX));
    formData.append("move_y", String(moveY));
    formData.append("remove_bg", "false");
    return formData;
  };

  const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, value));

  const nudge = (
    setter: Dispatch<SetStateAction<number>>,
    delta: number,
    min: number,
    max: number
  ) => {
    setter((current) => Number(clamp(current + delta, min, max).toFixed(2)));
  };

  const requestPreview = async (signal?: AbortSignal) => {
    if (!canProcess) {
      return;
    }

    setPreviewBusy(true);
    setStatus("Actualizando vista previa...");

    try {
      const response = await fetch(`${API_URL}/preview`, {
        method: "POST",
        body: buildFormData(),
        signal,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail ?? "Error generando vista previa");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl((old: string) => {
        if (old) {
          URL.revokeObjectURL(old);
        }
        return url;
      });

      setStatus("Vista previa actualizada");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      const message = error instanceof Error ? error.message : "Error inesperado";
      setStatus(message);
    } finally {
      setPreviewBusy(false);
    }
  };

  useEffect(() => {
    if (!canProcess) {
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void requestPreview(controller.signal);
    }, 180);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [canProcess, frame, imageFile, moveX, moveY, zoom]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const exportZip = async () => {
    if (!canProcess) {
      return;
    }

    setBusy(true);
    setStatus("Creando ZIP...");

    try {
      const response = await fetch(`${API_URL}/export`, {
        method: "POST",
        body: buildFormData(),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail ?? "Error exportando ZIP");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "icon-forge-export.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);

      setStatus("ZIP descargado");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Error inesperado";
      setStatus(message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page">
      <section className="panel">
        <h1>ICON</h1>
        <p className="subtitle">Crea iconos para macOS, Windows, iOS y Android desde una sola imagen.</p>

        <label className="field">
          <span>1) Para que plataforma quieres el icono</span>
          <select value={platform} onChange={(e: ChangeEvent<HTMLSelectElement>) => setPlatform(e.target.value as Platform)}>
            {(Object.keys(platformLabels) as Platform[]).map((key) => (
              <option key={key} value={key}>
                {platformLabels[key]}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>2) Agrega tu imagen</span>
          <input type="file" accept="image/png,image/jpeg,image/webp" onChange={onFileChange} />
        </label>

        <label className="field">
          <span>3) Frame (corte del icono)</span>
          <select value={frame} onChange={(e: ChangeEvent<HTMLSelectElement>) => setFrame(e.target.value as Frame)}>
            <option value="rounded">Rounded (recomendado)</option>
            <option value="circle">Circle</option>
            <option value="square">Square</option>
          </select>
        </label>

        <div className="field">
          <span>4) Ajusta la imagen dentro del frame</span>
          <label>
            Zoom: {zoom.toFixed(2)}x
            <div className="nudge-row">
              <button type="button" className="mini-btn" onClick={() => nudge(setZoom, -0.01, 0.5, 3)}>-</button>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.01"
                value={zoom}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setZoom(Number(e.target.value))}
              />
              <button type="button" className="mini-btn" onClick={() => nudge(setZoom, 0.01, 0.5, 3)}>+</button>
            </div>
          </label>
          <label>
            Mover horizontal: {moveX.toFixed(2)}
            <div className="nudge-row">
              <button type="button" className="mini-btn" onClick={() => nudge(setMoveX, -0.01, -1, 1)}>-</button>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.01"
                value={moveX}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setMoveX(Number(e.target.value))}
              />
              <button type="button" className="mini-btn" onClick={() => nudge(setMoveX, 0.01, -1, 1)}>+</button>
            </div>
          </label>
          <label>
            Mover vertical: {moveY.toFixed(2)}
            <div className="nudge-row">
              <button type="button" className="mini-btn" onClick={() => nudge(setMoveY, -0.01, -1, 1)}>-</button>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.01"
                value={moveY}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setMoveY(Number(e.target.value))}
              />
              <button type="button" className="mini-btn" onClick={() => nudge(setMoveY, 0.01, -1, 1)}>+</button>
            </div>
          </label>
          <button type="button" onClick={() => { setZoom(1); setMoveX(0); setMoveY(0); }}>
            Reset ajuste
          </button>
        </div>

        <div className="actions">
          <button onClick={exportZip} disabled={!canProcess || busy}>Exportar ZIP</button>
        </div>

        <p className="status">{previewBusy ? "Vista previa en vivo..." : status}</p>
      </section>

      <section className="preview">
        <h2>Vista previa</h2>
        {previewUrl ? <img src={previewUrl} alt="Vista previa del icono" /> : <div className="placeholder">Sin vista previa</div>}
      </section>
    </main>
  );
}

export default App;
