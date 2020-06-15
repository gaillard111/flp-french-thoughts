<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Application\Sonata\UserBundle\Entity\User;
use FOS\UserBundle\Form\Type\RegistrationFormType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolverInterface;

/**
 * Class RegisterType
 *
 * @package Application\Sonata\UserBundle\Form\Type
 */
class RegisterType extends RegistrationFormType
{
    /**
     * @param FormBuilderInterface $builder
     * @param array                $options
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            /*->add('username', null, array(
                'label'    => 'user.form.registration.username.label',
            ))*/
            ->add('email', 'email', [
                'label'      => 'user.form.registration.email.label',
                'label_attr' => [
                    'class' => 'col-sm-2',
                ],
            ])
            ->add('firstname', null, [
                'label'      => 'user.form.registration.firstname.label',
                'label_attr' => [
                    'class' => 'col-sm-2',
                ],
                'required' => true,
            ])
            ->add('lastname', null, [
                'label'      => 'user.form.registration.lastname.label',
                'label_attr' => [
                    'class' => 'col-sm-2',
                ],
                'required' => true,
            ])
            ->add('plainPassword', 'repeated', [
                'type'          => 'password',
                'first_options' => [
                    'label'      => 'user.form.registration.password.label',
                    'label_attr' => [
                        'class' => 'col-sm-2',
                    ],
                ],
                'second_options' => [
                    'label'      => 'user.form.registration.verification.label',
                    'label_attr' => [
                        'class' => 'col-sm-2',
                    ],
                ],
                'invalid_message' => 'user.form.registration.password.mismatch',

            ])
            ->add('roles', 'choice', [
                'label' => 'Type Account',
                'label_attr' => [
                    'class' => 'col-sm-2',
                ],
                'choices' => [
                    'student' => 'Student',
                    'user'    => 'User',
                ],
                'expanded' => true,
                'mapped'   => false,
//                'required' => false,
            ])
            ->add('reCaptcha', 'hidden', [
                'mapped' => false,
                'attr'   => [
                    'class' => 'g-recaptcha',
                ],
            ])
        ;
    }

    /**
     * @param OptionsResolverInterface $resolver
     */
    public function setDefaultOption(OptionsResolverInterface $resolver)
    {
        $resolver->setDefaults([
            'validation_groups' => ['CustomRegistration'],
            'data_class'        => User::class,
        ]);
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'front_user_registration';
    }
}