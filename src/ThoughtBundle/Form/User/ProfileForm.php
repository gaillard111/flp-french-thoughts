<?php

namespace ThoughtBundle\Form\User;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\EmailType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class ProfileForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('email', EmailType::class, [

            ])
            ->add('username', EmailType::class, [

            ])
            ->add('firstname', TextType::class, [

            ])
            ->add('lastname', TextType::class, [

            ])
            ->add('Save', SubmitType::class, [
                'attr' => [
                    'class' => 'btn-info',
                ],
            ])
        ;
    }

    /**
     * @inheritdoc
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => 'Application\Sonata\UserBundle\Entity\User',
        ]);
    }
}