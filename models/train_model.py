"""
CNN Model Training Pipeline.
Trains a convolutional neural network on captured face images.
Supports data augmentation, early stopping, and model checkpointing.
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, regularizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Add parent to path so config is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


def build_cnn_model(num_classes, img_size=128):
    """
    Build a CNN model for face classification.
    Architecture: 3x Conv blocks → GlobalAveragePooling → Dense → Dropout → Softmax
    """
    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same',
                      input_shape=(img_size, img_size, 3)),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Classifier head
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu',
                     kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model


def train_model(dataset_path=None, models_path=None, img_size=None, epochs=40):
    """
    Train the CNN on the student face dataset.
    Returns dict with training results and label_map.
    """
    dataset_path = dataset_path or Config.DATASET_PATH
    models_path = models_path or Config.MODELS_PATH
    img_size = img_size or Config.IMAGE_SIZE

    os.makedirs(models_path, exist_ok=True)
    os.makedirs(dataset_path, exist_ok=True)

    # Collect classes (student IDs with >= MIN_FACE_IMAGES images)
    classes = []
    all_dirs = []
    try:
        all_dirs = sorted(os.listdir(dataset_path))
    except Exception as e:
        return {'success': False, 'message': f'Cannot read dataset folder: {e}', 'classes': []}

    for d in all_dirs:
        dpath = os.path.join(dataset_path, d)
        if os.path.isdir(dpath):
            count = len([f for f in os.listdir(dpath) if f.lower().endswith('.jpg')])
            print(f'[Training] Student [{d}]: {count} images')
            if count >= Config.MIN_FACE_IMAGES:
                classes.append(d)
            else:
                print(f'[Training] Skipping [{d}] - only {count} images (need {Config.MIN_FACE_IMAGES})')

    if len(classes) < 1:
        total_students = len([d for d in all_dirs
                               if os.path.isdir(os.path.join(dataset_path, d))])
        if total_students == 0:
            msg = ('No student data found. Please add students and capture '  
                   'face images first using Students > Add Student.')
        else:
            msg = (f'Found {total_students} student folder(s) but none has '
                   f'{Config.MIN_FACE_IMAGES}+ images. Capture more face images first.')
        return {'success': False, 'message': msg, 'classes': classes}

    print(f"[Training] Found {len(classes)} students: {classes}")

    # Build label map: index → student_id
    label_map = {i: sid for i, sid in enumerate(classes)}
    np.save(os.path.join(models_path, 'label_map.npy'), label_map)

    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1.0/255,
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        brightness_range=[0.7, 1.3],
        validation_split=0.2
    )

    train_gen = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(img_size, img_size),
        batch_size=32,
        class_mode='categorical',
        subset='training',
        shuffle=True,
        classes=classes
    )

    val_gen = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(img_size, img_size),
        batch_size=32,
        class_mode='categorical',
        subset='validation',
        shuffle=False,
        classes=classes
    )

    # Build model
    model = build_cnn_model(num_classes=len(classes), img_size=img_size)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    model_checkpoint_path = os.path.join(models_path, 'face_model.h5')
    cb_list = [
        callbacks.EarlyStopping(monitor='val_accuracy', patience=8, restore_best_weights=True, verbose=1),
        callbacks.ModelCheckpoint(model_checkpoint_path, monitor='val_accuracy',
                                   save_best_only=True, verbose=1),
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=4, min_lr=1e-6, verbose=1),
    ]

    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=cb_list,
        verbose=1
    )

    # Save training history
    hist_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(os.path.join(models_path, 'training_history.json'), 'w') as f:
        json.dump(hist_dict, f, indent=2)

    final_acc = max(history.history.get('val_accuracy', [0]))
    
    return {
        'success': True,
        'message': f'Model trained successfully! Best val accuracy: {final_acc:.2%}',
        'classes': classes,
        'num_classes': len(classes),
        'best_accuracy': round(final_acc * 100, 2),
        'epochs_trained': len(history.history['accuracy'])
    }


if __name__ == '__main__':
    print("=== CNN Training Pipeline ===")
    result = train_model()
    print(result)
