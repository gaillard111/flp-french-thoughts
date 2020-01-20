<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Symfony\Bridge\Doctrine\Form\Type\EntityType;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\CheckboxType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

/**
 * Class ChainType
 *
 * @package Application\Sonata\UserBundle\Form\Type
 */
class ChainType extends AbstractType
{
    /**
     * @param FormBuilderInterface $builder
     * @param array                $options
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('name', TextType::class, [
                'label_attr' => [
                    'class' => 'control-label col-sm-2',
                ],
                'attr' => [
                    'class'       => 'form-control',
                    'placeholder' => 'chain.property.name.placeholder',
                ],
                'label' => 'chain.property.name.label',
            ])
            ->add('topic', EntityType::class, [
                'class'        => 'ThoughtBundle\Entity\Topic',
                'choice_label' => 'name',
                'label_attr'   => [
                    'class' => 'control-label col-sm-2 topic-select',
                ],
                'attr' => [
                    'class' => 'form-control topic-select',
                ],
                'required' => false,
            ])
            ->add('isPrivate', CheckboxType::class, [
                'label'      => 'Private',
                'label_attr' => [
                    'class' => 'control-label col-sm-2',

                ],
                'required' => false,
                'attr'     => [
                    'class' => 'private',
                ],
            ])
            ->add('isCollective', CheckboxType::class, [
                'label'      => 'Collective',
                'label_attr' => [
                    'class' => 'control-label col-sm-2 collective',

                ],
                'required' => false,
                'attr'     => [
                    'class' => 'collective',
                ],
            ])
            ->add('submit', SubmitType::class, [
                'label' => 'user.chain.edit_page.submit',
                'attr'  => [
                    'class' => 'btn btn-success pull-right',
                ],
            ])
        ;
    }

    /**
     * @param OptionsResolver $resolver
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => 'ThoughtBundle\Entity\Chain',
            'attr'       => [
                'class' => 'form-horizontal',
            ],
        ]);
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'sonata_user_chain_create';
    }
}
