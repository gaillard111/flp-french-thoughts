<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Symfony\Component\Form\AbstractType;
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
            ->add('name', 'text', array(
                'label_attr'  => array('class' => 'control-label col-sm-2'),
                'attr'        => array(
                    'class'       => 'form-control',
                    'placeholder' => 'chain.property.name.placeholder',
                ),
                'label'       => 'chain.property.name.label',
                'constraints' => array(
                    new NotBlank(array(
                        'message' => 'chain.property.name.not_blank',
                    )),
                ),
            ))
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
