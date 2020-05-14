<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtType
 *
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
            ->add('category', TextType::class, [
                'label_attr' => ['class' => 'control-label col-sm-2'],
                'attr'       => ['class' => 'form-control'],
                'label'      => 'thought.filter.fields.category.label',
            ])
            ->add('content', TextareaType::class, [
                'label_attr' => ['class' => 'control-label col-sm-2'],
                'attr'       => ['class' => 'form-control js-ckeditor'],
                'label'      => 'thought.filter.fields.content.label',
            ])
            ->add('thoughtInfo', TextType::class, [
                'label_attr' => ['class' => 'control-label col-sm-2'],
                'attr'       => ['class' => 'form-control'],
                'required'   => false,
                'label'      => 'thought.filter.fields.thoughtInfo.label',
            ])
            ->add('tags', TextType::class, [
                'label_attr' => ['class' => 'control-label col-sm-2'],
                'attr'       => ['class' => 'form-control', 'data-role' => 'tagsinput'],
                'required'   => false,
                'label'      => 'thought.filter.fields.tags.label',
            ])
            ->add('author', TextType::class, [
                'label_attr' => ['class' => 'control-label col-sm-2'],
                'attr'       => ['class' => 'form-control'],
                'label'      => 'thought.filter.fields.author.label',
            ])
        ;
    }

    /**
     * @param OptionsResolver $resolver
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => Thought::class,
        ]);
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'sonata_user_thought_create';
    }
}
