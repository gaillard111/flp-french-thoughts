<?php

namespace ThoughtBundle\Form\Teacher;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class GroupForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('title', 'text', [
                'attr' => [
                    'placeholder' => 'Title',
                    'oninvalid' => "setCustomValidity('Enter name for group')"
                ]
            ])
            ->add('topicNewLesson', 'textarea', [
                'required' => false,
                'attr' => [
                    'rows'=>'5',
                    'cols' => '60',
                    'maxlength' => '1000',
                    'placeholder' => 'teacher.create_group.topic_new_lesson',
                ]
            ])
        ;
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => 'ThoughtBundle\Entity\TeacherGroup',
        ]);
    }
}