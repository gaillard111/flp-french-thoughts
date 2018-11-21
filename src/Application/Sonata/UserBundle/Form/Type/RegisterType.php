<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Application\Sonata\UserBundle\Entity\User;
use FOS\UserBundle\Form\Type\RegistrationFormType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolverInterface;

/**
 * Class RegisterType
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
                'label'    => 'user.form.registration.email.label',
            ])
            ->add('firstname', null, [
                'label'    => 'user.form.registration.firstname.label',
                'required' => true,
            ])
            ->add('lastname', null, [
                'label'    => 'user.form.registration.lastname.label',
                'required' => true,
            ])
            ->add('plainPassword', 'repeated', [
                'type'            => 'password',
                'first_options'   => ['label' => 'user.form.registration.password.label'],
                'second_options'  => ['label' => 'user.form.registration.verification.label'],
                'invalid_message' => 'user.form.registration.password.mismatch',
            ])
            ->add('reCaptcha', 'hidden', [
                'mapped'    =>  false,
                'attr'      =>  [
                    'class'     =>  'g-recaptcha'
                ]
            ])
        ;
    }

    /**
     * @param OptionsResolverInterface $resolver
     */
    public function setDefaultOption(OptionsResolverInterface $resolver)
    {
        $resolver->setDefaults(array(
            'validation_groups' => array('CustomRegistration'),
            'data_class'        => User::class
        ));
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'front_user_registration';
    }
}