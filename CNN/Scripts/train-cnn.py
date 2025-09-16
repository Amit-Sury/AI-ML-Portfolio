
#Import required packages

import argparse
import os
import tensorflow

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Dropout, Input
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--batch-size', type=int, default=32)

    # Directories provided by SageMaker
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--training', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--validation', type=str, default=os.environ['SM_CHANNEL_VALIDATION'])

    args, _ = parser.parse_known_args()

    # Notice earlier the variable names were defined with hyphen but below we're using 
    # underscore, it automatically gets converted to underscore in argparse
    epochs     = args.epochs
    lr         = args.learning_rate
    batch_size = args.batch_size
    model_dir  = args.model_dir
    training_dir   = args.training
    validation_dir = args.validation

    img_size = (128, 128)

    #Applying data augmentation on training dataset
    train_datagen = ImageDataGenerator(
    rescale=1./255, #pixel values go from [0,255] → [0,1] (normalization)
    rotation_range=20, #randomly rotate images up to ±20°.
    width_shift_range=0.2, #randomly shift images horizontally (20% of width)
    height_shift_range=0.2, #randomly shift vertically (20% of height)
    shear_range=0.2, #applies shearing (like slanting the image)
    zoom_range=0.2, #randomly zoom in/out
    horizontal_flip=True #flips images left–right
    )

    #This is for validation dataset, only rescaling is done. 
    #No augmentation ensures validation accuracy is tested on clean, untouched images.
    val_datagen = ImageDataGenerator(rescale=1./255)

    #Loads images from training folder
    train_gen = train_datagen.flow_from_directory(
        training_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical" 
    )

    #Loads images from validation folder
    val_gen = val_datagen.flow_from_directory(
        validation_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical"
    )
    
    #Print indices of 3 classes based on the labels (Dog, Horse, Elephant)
    print(train_gen.class_indices)

    #input images are 128x128 RGB
    input_shape=(128,128,3)

    model = Sequential()

    # 32 filters, 3x3 kernel, ReLU, input images are 128x128 RGB
    model.add(Conv2D(32, (3,3), activation="relu", input_shape=input_shape))
    model.add(MaxPooling2D((2,2)))

    # second conv layer with 64 filters
    model.add(Conv2D(64, (3,3), activation="relu"))
    model.add(MaxPooling2D((2,2)))

    #Adding an additional dropout to tackle overfitting issue
    model.add(Dropout(0.2))

    # third conv layer with 128 filters. We increased the filter in each layer 
    model.add(Conv2D(128, (3,3), activation="relu"))
    model.add(MaxPooling2D((2,2)))

    #Adding an additional dropout to tackle overfitting issue
    model.add(Dropout(0.2))
    
    #adding additional layer to try improving accuracy
    model.add(Conv2D(256, (3,3), activation="relu"))   
    model.add(MaxPooling2D((2,2)))


    # flatten feature maps → 1D vector
    model.add(Flatten())
    # fully connected layer with 128 neurons
    model.add(Dense(128, activation="relu"))
    # randomly drop 50% neurons to prevent overfitting
    model.add(Dropout(0.5))

    # output layer for 3 classes (Dog, Horse, Elephant)
    model.add(Dense(3, activation="softmax"))   # 3 classes: Dog, Horse, Elephant

    #Print model summary
    print(model.summary())

    model.compile(loss=tensorflow.keras.losses.categorical_crossentropy,
                  optimizer=Adam(learning_rate=lr),
                  metrics=['accuracy'])

    #Add early stopping
    early_stop = EarlyStopping(
    monitor='val_loss',   # you can also monitor 'val_accuracy'
    patience=5,           # stop if no improvement after 5 epochs
    restore_best_weights=True  # rollback to best weights
    )

    #Train Model
    model.fit(train_gen, validation_data=val_gen, 
              epochs=epochs, callbacks=[early_stop],
              verbose=2)
    
    score = model.evaluate(val_gen, verbose=0)
    print('Validation loss    :', score[0])
    print('Validation accuracy:', score[1])

    # Save model for SageMaker hosting
    model.save(os.path.join(model_dir, "1"))
