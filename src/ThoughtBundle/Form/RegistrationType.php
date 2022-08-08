<?php

namespace ThoughtBundle\Form;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\CheckboxType;
use Symfony\Component\Form\FormBuilderInterface;

class RegistrationType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->remove('username')
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
            ->add('termsOfService', CheckboxType::class, [
                'mapped' => false,
                'required' => false,
                'label' => "J'accepte les mention légales",
            ])
            ->add('receiveEmails', CheckboxType::class, [
                'required' => false,
                'label' => "J'accepte de recevoir des e-mails"
            ])
            ->add('roles', 'choice', [
                'label'      => 'Account Type',
                'data' => 'user',
                'label_attr' => [
                    'class' => 'col-sm-2',
                ],
                'choices' => [
                    'student' => 'S\'enregistrer comme étudiant',
                    'teacher' => 'S\'enregistrer comme enseignant/e',
                    'user'    => 'S\'enregistrer normalement',
                ],
                'expanded' => true,
                'mapped'   => false,
            ])
        ;
    }

    public function getParent()
    {
        return 'FOS\UserBundle\Form\Type\RegistrationFormType';
    }

    public function getBlockPrefix()
    {
        return 'app_user_registration';
    }

    // For Symfony 2.x
    public function getName()
    {
        return $this->getBlockPrefix();
    }
}