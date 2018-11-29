<?php

namespace Application\Sonata\UserBundle\Form\Type;

use function Sodium\add;
use Sonata\AdminBundle\Form\Type\Filter\ChoiceType;
use Symfony\Bridge\Doctrine\Form\Type\EntityType;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\CheckboxType;
use Symfony\Component\Form\Extension\Core\Type\RadioType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use Symfony\Component\Validator\Constraints\NotBlank;

/**
 * Class ChainType
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
            ->add('name', 'text', [
                'label_attr'    => [
                    'class'       => 'control-label col-sm-2'
                ],
                'attr'          => [
                    'class'       => 'form-control',
                    'placeholder' => 'chain.property.name.placeholder',
                ],
                'label'         => 'chain.property.name.label',
                'constraints'   => [
                    new NotBlank([
                        'message' => 'chain.property.name.not_blank',
                    ]),
                ]
            ])
            ->add('topic', EntityType::class, [
                'class'         =>  'ThoughtBundle\Entity\Topic',
                'choice_label'  =>  'name',
                'label_attr'    =>  [
                    'class'       =>  'control-label col-sm-2'
                ],
                'attr'          =>  [
                    'class'       => 'form-control',
                ],
                'required'      =>  false
            ])
            ->add('isPrivate', CheckboxType::class, [
                'label'         =>  'Private',
                'label_attr'    =>  [
                    'class'       =>  'control-label col-sm-2',

                ],
                'required'      =>  false,
                'attr'          =>  [
                    'class'        =>  'private',
                ],
            ])
            ->add('isCollective', CheckboxType::class, [
                'label'         =>  'Collective',
                'label_attr'    =>  [
                    'class'       =>  'control-label col-sm-2 collective',

                ],
                'required'      =>  false,
                'attr'          =>  [
                    'class'        =>  'collective',
                ],
            ])
        ;
    }

    /**
     * @param OptionsResolver $resolver
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults(array(
            'data_class' => 'ThoughtBundle\Entity\Chain',
        ));
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'sonata_user_chain_create';
    }
}
