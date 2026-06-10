import { useEffect, useState } from "react";
import { apiJson } from "../lib/api";
import type { AlbumRecord, PhotoRecord } from "../lib/types";

export function PhotosPage() {
  const [photos, setPhotos] = useState<PhotoRecord[]>([]);
  const [albums, setAlbums] = useState<AlbumRecord[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [albumName, setAlbumName] = useState("Family frame");
  const [mode, setMode] = useState("fit");
  const [message, setMessage] = useState("Ready");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [photoPayload, albumPayload] = await Promise.all([
      apiJson<{ photos: PhotoRecord[] }>("/api/photos"),
      apiJson<{ albums: AlbumRecord[] }>("/api/albums")
    ]);
    setPhotos(photoPayload.photos);
    setAlbums(albumPayload.albums);
  };

  useEffect(() => {
    load().catch((error: Error) => setMessage(error.message));
  }, []);

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    form.append("mode", mode);
    try {
      const result = await apiJson<{ accepted: number; errors: unknown[] }>("/api/photos/batch", { method: "POST", body: form });
      setMessage(`Processed ${result.accepted} photo${result.accepted === 1 ? "" : "s"}.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const createAlbum = async () => {
    const photo_ids = Array.from(selected).map((id) => Number(id));
    await apiJson("/api/albums", {
      method: "POST",
      body: JSON.stringify({ name: albumName, mode: "ordered", photo_ids })
    });
    setMessage(`Created album with ${photo_ids.length} photo${photo_ids.length === 1 ? "" : "s"}.`);
    setSelected(new Set());
    await load();
  };

  const deletePhoto = async (id: string) => {
    await apiJson(`/api/photos/${id}`, { method: "DELETE" });
    setSelected((current) => {
      const next = new Set(current);
      next.delete(id);
      return next;
    });
    await load();
  };

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Manage Photos</h1>
          <p>Upload photos, generate ePaper previews and raw frames, then group them into display playlists.</p>
        </div>
      </header>

      <section className="workflow-panel">
        <div className="form-row">
          <label>
            Process mode
            <select value={mode} onChange={(event) => setMode(event.target.value)}>
              <option value="fit">Fit</option>
              <option value="fill">Fill</option>
              <option value="crop">Crop</option>
            </select>
          </label>
          <label className="file-button">
            <input type="file" accept="image/*" multiple onChange={(event) => void upload(event.currentTarget.files)} />
            {busy ? "Processing..." : "Upload photos"}
          </label>
          <span className="muted-text">{message}</span>
        </div>
      </section>

      <section className="content-layout">
        <div className="card-grid">
          {photos.map((photo) => (
            <article key={photo.id} className="asset-card">
              <button
                className={selected.has(photo.id) ? "asset-select selected" : "asset-select"}
                onClick={() =>
                  setSelected((current) => {
                    const next = new Set(current);
                    if (next.has(photo.id)) next.delete(photo.id);
                    else next.add(photo.id);
                    return next;
                  })
                }
              >
                {photo.preview_url ? <img src={photo.preview_url} alt="" /> : <div className="preview-placeholder" />}
              </button>
              <div className="asset-meta">
                <strong>{photo.original_filename}</strong>
                <span>{photo.processed_status} · {photo.palette ?? "pending"}</span>
                <span>{photo.width && photo.height ? `${photo.width} x ${photo.height}` : "waiting"}</span>
              </div>
              <button className="secondary-button" onClick={() => void deletePhoto(photo.id)}>Delete</button>
            </article>
          ))}
          {!photos.length && (
            <section className="empty-state compact">
              <h2>No photos yet</h2>
              <p>Upload a batch to create previews and display-ready raw frames.</p>
            </section>
          )}
        </div>

        <aside className="side-stack">
          <section className="info-panel vertical">
            <h2>Playlist</h2>
            <p>{selected.size} selected</p>
            <label>
              Album name
              <input value={albumName} onChange={(event) => setAlbumName(event.target.value)} />
            </label>
            <button className="primary-button" disabled={!selected.size} onClick={() => void createAlbum()}>
              Create album
            </button>
          </section>
          <section className="info-panel vertical">
            <h2>Albums</h2>
            {albums.map((album) => (
              <div className="row-item" key={album.id}>
                <span>{album.name}</span>
                <strong>{album.item_count}</strong>
              </div>
            ))}
            {!albums.length && <p>No albums yet.</p>}
          </section>
        </aside>
      </section>
    </div>
  );
}
