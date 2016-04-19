<?php

namespace ThoughtBundle\Form;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class SearchFilterType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('words', 'text', array(
                'mapped' => false,
            ))
            ->add('fields', 'choice', array(
                'mapped' => false,
                'expanded' => true,
                'multiple' => true,
                'choices' => array(
                    'content'     => 'content',
                    'category'    => 'category',
                    'tags'        => 'tags',
                    'author'      => 'author',
                    'thoughtInfo' => 'thoughtInfo',
                ),
            ))
        ;
    }

    public function configureOptions(OptionsResolver $resolver)
    {

    }

    public function getName()
    {
        return 'thought_bundlesearch_filter_type';
    }
}
