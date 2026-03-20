#!/usr/bin/env python3
"""
Скрипт для создания тестовых PDF файлов для PaperQA2.
Содержит 6 научных статей по машинному обучению.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER
import os

OUTPUT_DIR = "/home/homo/projects/boaai_s/test_papers"

def create_pdf(filename, title, content_pages):
    """Создаёт PDF файл с заданным содержимым."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Заголовок
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Страницы контента
    for page in content_pages:
        for para_text in page:
            p = Paragraph(para_text, styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 0.15*inch))
        story.append(PageBreak())
    
    doc.build(story)
    print(f"✓ Создан: {filename}")


def create_transformer_paper():
    """Статья 1: Transformer и механизм внимания."""
    title = "Self-Attention Mechanisms in Transformer Architectures"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "This paper presents a comprehensive analysis of self-attention mechanisms "
            "in transformer architectures. We demonstrate that self-attention allows "
            "for parallelization of sequence processing, overcoming limitations of RNNs."
        ],
        # Страница 2
        [
            "<b>1. Introduction</b><br/>"
            "Recurrent Neural Networks (RNNs) have been the dominant architecture for "
            "sequence modeling. However, RNNs suffer from sequential computation, making "
            "them slow to train on long sequences."
        ],
        # Страница 3
        [
            "<b>2. Self-Attention Mechanism</b><br/>"
            "The self-attention mechanism computes attention scores between all pairs "
            "of positions in a sequence. This allows the model to directly capture "
            "long-range dependencies without sequential processing."
        ],
        # Страница 4
        [
            "<b>3. Advantages over RNNs</b><br/>"
            "Key advantages include: (1) Parallel computation across sequence positions, "
            "(2) Constant path length between any two positions, (3) Better gradient flow "
            "during training. Our experiments show 10x speedup compared to LSTM."
        ],
        # Страница 5
        [
            "<b>4. Conclusion</b><br/>"
            "Self-attention mechanisms represent a significant advancement over RNNs "
            "for sequence modeling tasks. The parallelization capability and improved "
            "gradient flow make transformers the preferred architecture."
        ]
    ]
    create_pdf("01_transformer_attention.pdf", title, content)


def create_cnn_paper():
    """Статья 2: CNN для распознавания изображений."""
    title = "Convolutional Neural Networks for Image Recognition"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "We present a study of Convolutional Neural Networks (CNNs) for image "
            "recognition tasks. CNNs leverage spatial structure through convolution "
            "operations and pooling layers."
        ],
        # Страница 2
        [
            "<b>1. Architecture Overview</b><br/>"
            "CNNs consist of convolutional layers, pooling layers, and fully connected "
            "layers. The convolutional layers extract hierarchical features from images."
        ],
        # Страница 3
        [
            "<b>2. Convolutional Layers</b><br/>"
            "Each convolutional layer applies learnable filters to the input. Early "
            "layers detect edges and textures, while deeper layers capture semantic "
            "concepts like objects and scenes."
        ],
        # Страница 4
        [
            "<b>3. Pooling and Stride</b><br/>"
            "Pooling layers reduce spatial dimensions, providing translation invariance. "
            "Max pooling selects the maximum value in each region, preserving important "
            "features while reducing computation."
        ],
        # Страница 5
        [
            "<b>4. Results</b><br/>"
            "Our CNN architecture achieves 95.2% accuracy on ImageNet validation set. "
            "This demonstrates the effectiveness of deep convolutional architectures "
            "for visual recognition tasks."
        ]
    ]
    create_pdf("02_cnn_image_recognition.pdf", title, content)


def create_rl_paper():
    """Статья 3: Обучение с подкреплением."""
    title = "Deep Reinforcement Learning: Methods and Applications"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "This paper reviews deep reinforcement learning (RL) methods. We cover "
            "Q-learning, policy gradients, and actor-critic algorithms with applications "
            "to games and robotics."
        ],
        # Страница 2
        [
            "<b>1. Introduction to RL</b><br/>"
            "Reinforcement learning involves an agent interacting with an environment. "
            "The agent receives rewards and learns to maximize cumulative reward through "
            "trial and error."
        ],
        # Страница 3
        [
            "<b>2. Q-Learning and DQN</b><br/>"
            "Deep Q-Networks (DQN) combine Q-learning with deep neural networks. "
            "Experience replay and target networks stabilize training. DQN achieved "
            "superhuman performance on Atari games."
        ],
        # Страница 4
        [
            "<b>3. Policy Gradient Methods</b><br/>"
            "Policy gradient methods directly optimize the policy. REINFORCE and "
            "PPO algorithms show strong performance on continuous control tasks. "
            "PPO's clipped objective prevents destructive policy updates."
        ],
        # Страница 5
        [
            "<b>4. Actor-Critic Algorithms</b><br/>"
            "Actor-critic methods combine value and policy learning. The critic "
            "estimates value function, while the actor updates the policy. "
            "A3C and SAC are prominent examples with excellent sample efficiency."
        ]
    ]
    create_pdf("03_reinforcement_learning.pdf", title, content)


def create_gan_paper():
    """Статья 4: Генеративно-состязательные сети."""
    title = "Generative Adversarial Networks: Theory and Practice"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "Generative Adversarial Networks (GANs) consist of a generator and "
            "discriminator trained in competition. We review GAN variants and "
            "applications in image synthesis."
        ],
        # Страница 2
        [
            "<b>1. GAN Framework</b><br/>"
            "The generator creates fake samples from noise, while the discriminator "
            "distinguishes real from fake. This adversarial training produces "
            "high-quality synthetic data."
        ],
        # Страница 3
        [
            "<b>2. DCGAN and StyleGAN</b><br/>"
            "DCGAN introduced convolutional architectures to GANs. StyleGAN provides "
            "fine-grained control over generated images through style mixing and "
            "adaptive instance normalization."
        ],
        # Страница 4
        [
            "<b>3. Training Challenges</b><br/>"
            "GAN training suffers from mode collapse and instability. Techniques "
            "like gradient penalty, spectral normalization, and two-time-scale "
            "updates improve training stability."
        ],
        # Страница 5
        [
            "<b>4. Applications</b><br/>"
            "GANs excel at image-to-image translation, super-resolution, and "
            "data augmentation. CycleGAN enables unpaired image translation "
            "between domains without aligned training data."
        ]
    ]
    create_pdf("04_gan_generative_models.pdf", title, content)


def create_bert_paper():
    """Статья 5: BERT и языковые модели."""
    title = "BERT: Pre-trained Language Representations for NLP"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "BERT (Bidirectional Encoder Representations from Transformers) achieves "
            "state-of-the-art results on NLP tasks through pre-training on masked "
            "language modeling and next sentence prediction."
        ],
        # Страница 2
        [
            "<b>1. Pre-training Objectives</b><br/>"
            "BERT uses two objectives: (1) Masked Language Modeling (MLM) predicts "
            "masked tokens using bidirectional context, (2) Next Sentence Prediction "
            "(NSP) learns sentence relationships."
        ],
        # Страница 3
        [
            "<b>2. Architecture</b><br/>"
            "BERT uses transformer encoder layers with self-attention. BERT-base "
            "has 12 layers and 110M parameters. BERT-large has 24 layers and "
            "340M parameters."
        ],
        # Страница 4
        [
            "<b>3. Fine-tuning</b><br/>"
            "Pre-trained BERT can be fine-tuned for downstream tasks with minimal "
            "architecture changes. Single additional output layer enables classification, "
            "QA, and NER tasks."
        ],
        # Страница 5
        [
            "<b>4. Results</b><br/>"
            "BERT achieves SOTA on GLUE (80.5%), SQuAD (93.2% F1), and MNLI (86.7% "
            "accuracy). Fine-tuning requires significantly less data than training "
            "from scratch."
        ]
    ]
    create_pdf("05_bert_nlp_embeddings.pdf", title, content)


def create_optimizers_paper():
    """Статья 6: Сравнение оптимизаторов."""
    title = "Comparative Analysis of Deep Learning Optimizers"
    content = [
        # Страница 1
        [
            "<b>Abstract</b><br/>"
            "We compare popular optimization algorithms: SGD, Adam, RMSprop, and "
            "AdamW. Our analysis covers convergence speed, generalization, and "
            "hyperparameter sensitivity."
        ],
        # Страница 2
        [
            "<b>1. Stochastic Gradient Descent</b><br/>"
            "SGD with momentum remains a strong baseline. Learning rate scheduling "
            "and warm restarts improve convergence. SGD often finds flatter minima "
            "with better generalization."
        ],
        # Страница 3
        [
            "<b>2. Adam Optimizer</b><br/>"
            "Adam combines momentum and adaptive learning rates. Per-parameter "
            "adaptation accelerates training on sparse gradients. Adam converges "
            "faster but may generalize worse than SGD."
        ],
        # Страница 4
        [
            "<b>3. AdamW and Weight Decay</b><br/>"
            "AdamW decouples weight decay from gradient updates, improving "
            "generalization. Our experiments show AdamW consistently outperforms "
            "Adam on vision and language tasks."
        ],
        # Страница 5
        [
            "<b>4. Recommendations</b><br/>"
            "Use AdamW for fast prototyping and transformer models. Use SGD with "
            "momentum for CNNs when final accuracy is critical. Learning rate "
            "tuning is essential for all optimizers."
        ]
    ]
    create_pdf("06_optimizers_comparison.pdf", title, content)


def main():
    """Создать все тестовые PDF файлы."""
    print("Создание тестовых PDF файлов для PaperQA2...\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    create_transformer_paper()
    create_cnn_paper()
    create_rl_paper()
    create_gan_paper()
    create_bert_paper()
    create_optimizers_paper()
    
    print(f"\n✓ Готово! Создано 6 файлов в {OUTPUT_DIR}")
    print("\nТеперь вы можете запустить тесты:")
    print(f"  cd {OUTPUT_DIR}")
    print("  pqa ask 'Какие преимущества имеет механизм self-attention перед RNN?'")
    print("  pqa ask 'Сравните оптимизаторы Adam и SGD'")
    print("  pqa ask 'Какие архитектуры подходят для обработки последовательных данных?'")


if __name__ == "__main__":
    main()
