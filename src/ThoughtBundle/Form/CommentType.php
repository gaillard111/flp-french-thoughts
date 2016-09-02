<?php

namespace ThoughtBundle\Form;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use Symfony\Component\Validator\Constraints\Email;
use Symfony\Component\Validator\Constraints\NotBlank;

class CommentType extends AbstractType
{
    /**
     * @inheritdoc
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('name', 'text', array(
                'required' => false,
                'label'    => 'thought.comment.property.name.label',
                'label_attr' => array(
                    'class' => 'col-sm-3 control-label',
                ),
                'attr'     => array(
                    'class'       => 'form-control',
                    'placeholder' => 'thought.comment.property.name.placeholder',
                ),
            ))
            ->add('email', 'text', array(
                'label'    => 'thought.comment.property.email.label',
                'constraints' => array(
                    new Email(array(
                        'message' => 'thought.comment.property.email.email',
                    )),
                    new NotBlank(array(
                        'message' => 'thought.comment.property.email.not_blank',
                    )),
                ),
                'label_attr' => array(
                    'class' => 'col-sm-3 control-label',
                ),
                'attr' => array(
                    'class'       => 'form-control',
                    'placeholder' => 'thought.comment.property.email.placeholder',
                ),
            ))
            ->add('text', 'textarea', array(
                'attr' => array(
                    'class' => 'form-control',
                    'row'   => '3',
                ),
                'label_attr' => array(
                    'class' => 'col-sm-3 control-label',
                ),
                'label' => 'thought.comment.property.text.label',
                'constraints' => array(
                    new NotBlank(array(
                        'message' => 'thought.comment.property.text.not_blank',
                    )),
                ),
            ))
        ;
    }

    /**
     * @inheritdoc
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults(array(
            'data_class' => 'ThoughtBundle\Entity\Comment',
        ));
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'comment_quote';
    }
}
