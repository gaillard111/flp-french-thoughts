<?php

namespace ThoughtBundle\Form;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use ThoughtBundle\Entity\Topic;

class TopicSearchForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('name', TextType::class, [
                'required'           => false,
                'label'              => 'thought.topic.search_form.labels.name',
                'translation_domain' => 'messages',

            ])
            ->add('submit', SubmitType::class, [
                'label' => 'Go!',
                'attr'  => [
                    'class' => 'btn btn-info',
                ],
            ])
        ;
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver
            ->setDefaults([
                'data_class' => Topic::class,
            ]);
    }

    public function getBlockPrefix()
    {
        return 'thought_bundle_topic_search_form';
    }
}
