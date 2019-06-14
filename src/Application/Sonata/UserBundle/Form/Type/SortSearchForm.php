<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Application\Sonata\UserBundle\Form\Object\SearchObject;
use Symfony\Component\Form\Extension\Core\Type\ChoiceType;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\HiddenType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class SortSearchForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('searchString', TextType::class, [
                'required' => false,
                'label' => 'thought.search'
            ])
            ->add('sort', HiddenType::class, [
                'attr' => [
                    'class' => 'sort-hidden'
                ]
            ])
            ->add('submit', SubmitType::class, [
                'label' => 'Go!',
                'attr'  => [
                    'class'  => 'btn btn-info'
                ]
            ])
        ;
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => SearchObject::class,
            'attr'       => [
                'class' => 'search-form'
            ]
        ]);
    }

    public function getBlockPrefix()
    {
        return 'application_sonata_user_bundle_sort_search_form';
    }
}
