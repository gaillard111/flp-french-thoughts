<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

/**
 * Class ThoughtType
 * @package Application\Sonata\UserBundle\Form\Type
 */
class ThoughtType extends AbstractType
{
    /**
     * @param FormBuilderInterface $builder
     * @param array                $options
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('category', 'text', array(
                'label_attr' => array('class' => 'control-label col-sm-2'),
                'attr'       => array('class' => 'form-control'),
                'label'      => 'thought.filter.fields.category.label',
            ))
            ->add('content', 'textarea', array(
                'label_attr' => array('class' => 'control-label col-sm-2'),
                'attr'       => array('class' => 'form-control'),
                'label'      => 'thought.filter.fields.content.label',
            ))
            ->add('thoughtInfo', 'text', array(
                'label_attr' => array('class' => 'control-label col-sm-2'),
                'attr'       => array('class' => 'form-control'),
                'required'   => false,
                'label'      => 'thought.filter.fields.thoughtInfo.label',
            ))
            ->add('tags', 'text', array(
                'label_attr' => array('class' => 'control-label col-sm-2'),
                'attr'       => array('class' => 'form-control', 'data-role' => 'tagsinput'),
                'required'   => false,
                'label'      => 'thought.filter.fields.tags.label',
            ))
            ->add('author', 'text', array(
                'label_attr' => array('class' => 'control-label col-sm-2'),
                'attr'       => array('class' => 'form-control'),
                'label'      => 'thought.filter.fields.author.label',
            ))
        ;
    }

    /**
     * @param OptionsResolver $resolver
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults(array(
            'data_class' => 'ThoughtBundle\Entity\Thought',
        ));
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'sonata_user_thought_create';
    }
}
