import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

def build_model(input_dim, n_labels):
    import tensorflow as tf
    from tensorflow.keras import layers

    inputs = layers.Input(shape=(input_dim,))
    x = layers.Dense(256, activation="relu")(inputs)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(n_labels, activation="sigmoid")(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer="adam", loss="binary_crossentropy")
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emb", default="data/index/embeddings.npy")
    parser.add_argument("--emb-meta", default="data/index/embeddings_meta.json")
    parser.add_argument("--labels", default="data/labels.csv")
    parser.add_argument("--out", default="models/classifier")
    parser.add_argument("--epochs", type=int, default=30)
    args = parser.parse_args()

    emb_path = Path(args.emb)
    emb_meta_path = Path(args.emb_meta)
    labels_path = Path(args.labels)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not emb_path.exists() or not emb_meta_path.exists():
        raise FileNotFoundError("Embeddings or metadata not found. Run compute_embeddings.py first.")

    embeddings = np.load(str(emb_path))
    emb_meta = json.loads(emb_meta_path.read_text(encoding="utf-8"))
    meta_index = {item["chunk_id"]: item["index"] for item in emb_meta}

    if not labels_path.exists():
        raise FileNotFoundError(f"Labels CSV not found: {labels_path}")

    df = pd.read_csv(labels_path)
    # expect columns: file,chunk_id,labels (pipe-separated)
    df["labels"] = df["labels"].fillna("")
    df["label_list"] = df["labels"].apply(lambda s: [x.strip() for x in str(s).split("|") if x.strip()])

    # build label binarizer
    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    Y = mlb.fit_transform(df["label_list"])

    # build X by mapping chunk_ids to embeddings
    X = []
    rows = []
    for i, row in df.iterrows():
        cid = row["chunk_id"]
        if cid in meta_index:
            idx = meta_index[cid]
            X.append(embeddings[idx])
            rows.append(i)

    if len(X) == 0:
        raise RuntimeError("No labeled chunk_ids matched embeddings. Check labels CSV and embeddings meta.")

    X = np.vstack(X)
    Y = Y[rows]

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    model = build_model(input_dim=X.shape[1], n_labels=Y.shape[1])

    import tensorflow as tf
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(filepath=str(out_dir / "best_model.h5"), save_best_only=True)
    ]

    model.fit(X_train, y_train, validation_split=0.1, epochs=args.epochs, batch_size=32, callbacks=callbacks)

    # save model and label mapping
    model.save(str(out_dir / "model_saved"))
    (out_dir / "labels.json").write_text(json.dumps(mlb.classes_.tolist(), ensure_ascii=False, indent=2), encoding="utf-8")

    # evaluation
    y_pred = model.predict(X_test)
    y_pred_bin = (y_pred >= 0.5).astype(int)

    from sklearn.metrics import classification_report
    report = classification_report(y_test, y_pred_bin, target_names=mlb.classes_)
    print("Classification report:\n", report)


if __name__ == "__main__":
    main()
