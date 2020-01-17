<?php

namespace ThoughtBundle\Form;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use Symfony\Component\Validator\Constraints\NotBlank;

/**
 * Class ChainCommentType
 * @package ThoughtBundle\Form
 */
class ChainCommentType extends AbstractType
{
    /**
     * @inheritdoc
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('text', 'textarea', [
                'attr' => [
                    'class' => 'form-control',
                    'row'   => '3',
                ],
                'label' => 'thought.chain.comment.property.text.label',
                'constraints' => [
                    new NotBlank([
                        'message' => 'thought.chain.comment.property.text.not_blank',
                    ]),
                ],
            ])
        ;
    }

    /**
     * @inheritdoc
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => 'ThoughtBundle\Entity\ChainComment',
        ]);
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'chain_comment';
    }
}
